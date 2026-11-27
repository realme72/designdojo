from __future__ import annotations

import heapq
import itertools
import threading
from dataclasses import dataclass

from contract import Clock, DuplicateJob, InvalidInterval, InvalidTime, JobInfo, Scheduler, UnknownJob

from .schedules import Every, Once, Schedule, Times


@dataclass
class Job:
    id: str
    schedule: Schedule
    next_run: int
    paused: bool = False
    version: int = 0  # set from a global counter on every reschedule; stale heap entries are skipped


class HeapScheduler(Scheduler):
    def __init__(self, clock: Clock):
        self._clock = clock
        self._jobs: dict[str, Job] = {}
        self._heap: list[tuple[int, str, int]] = []
        self._versions = itertools.count(1)  # global, so a reused id never matches an old entry
        self._lock = threading.Lock()

    def _push(self, job: Job) -> None:
        job.version = next(self._versions)
        heapq.heappush(self._heap, (job.next_run, job.id, job.version))

    def _add(self, job_id: str, first: int, schedule: Schedule) -> None:
        with self._lock:
            if first < self._clock.now():
                raise InvalidTime(first)
            if job_id in self._jobs:
                raise DuplicateJob(job_id)
            job = Job(job_id, schedule, first)
            self._jobs[job_id] = job
            self._push(job)

    def schedule_once(self, job_id: str, run_at: int) -> None:
        self._add(job_id, run_at, Once())

    def schedule_every(self, job_id: str, start_at: int, interval_seconds: int) -> None:
        if interval_seconds < 1:
            raise InvalidInterval(interval_seconds)
        self._add(job_id, start_at, Every(start_at, interval_seconds))

    def schedule_times(self, job_id: str, start_at: int, interval_seconds: int, times: int) -> None:
        if interval_seconds < 1 or times < 1:
            raise InvalidInterval(f"{interval_seconds}s x{times}")
        self._add(job_id, start_at, Times(start_at, interval_seconds, times))

    def tick(self) -> list[str]:
        ran: list[str] = []
        with self._lock:
            now = self._clock.now()
            while self._heap and self._heap[0][0] <= now:
                _, job_id, version = heapq.heappop(self._heap)
                job = self._jobs.get(job_id)
                if job is None or job.version != version or job.paused:
                    continue
                ran.append(job_id)
                nxt = job.schedule.after_run(now)
                if nxt is None:
                    del self._jobs[job_id]
                else:
                    job.next_run = nxt
                    self._push(job)
        return ran

    def cancel(self, job_id: str) -> bool:
        with self._lock:
            return self._jobs.pop(job_id, None) is not None

    def _job(self, job_id: str) -> Job:
        job = self._jobs.get(job_id)
        if job is None:
            raise UnknownJob(job_id)
        return job

    def pause(self, job_id: str) -> None:
        with self._lock:
            self._job(job_id).paused = True

    def resume(self, job_id: str) -> None:
        with self._lock:
            job = self._job(job_id)
            if job.paused:
                job.paused = False
                job.next_run = job.schedule.on_resume(self._clock.now(), job.next_run)
                self._push(job)

    def pending(self) -> list[JobInfo]:
        with self._lock:
            active = [j for j in self._jobs.values() if not j.paused]
            return [JobInfo(j.id, j.next_run) for j in sorted(active, key=lambda j: (j.next_run, j.id))]
