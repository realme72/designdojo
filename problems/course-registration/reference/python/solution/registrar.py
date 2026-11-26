from __future__ import annotations

import threading
from collections import deque
from dataclasses import dataclass, field
from typing import Callable

from contract import (AlreadyCompleted, AlreadyRegistered, DuplicateCourse, EnrollmentStatus, InvalidCapacity,
                      MissingPrerequisite, NotRegistered, Registrar, TooManyCourses, UnknownCourse)


@dataclass
class Course:
    id: str
    capacity: int
    prerequisites: list[str]
    enrolled: set[str] = field(default_factory=set)
    waiting: deque[str] = field(default_factory=deque)


@dataclass
class Student:
    id: str
    completed: set[str] = field(default_factory=set)
    enrolled: set[str] = field(default_factory=set)


class University(Registrar):
    def __init__(self, max_courses: int):
        self._max = max_courses
        self._courses: dict[str, Course] = {}
        self._students: dict[str, Student] = {}
        self._lock = threading.Lock()  # one lock: seats and per-student limits span courses
        self._rules: list[Callable[[Student, Course], None]] = [
            self._not_completed, self._not_registered, self._prerequisites_met]

    # ---- eligibility chain (registration) ----
    def _not_completed(self, s: Student, c: Course) -> None:
        if c.id in s.completed:
            raise AlreadyCompleted(c.id)

    def _not_registered(self, s: Student, c: Course) -> None:
        if s.id in c.enrolled or s.id in c.waiting:
            raise AlreadyRegistered(c.id)

    def _prerequisites_met(self, s: Student, c: Course) -> None:
        missing = [p for p in c.prerequisites if p not in s.completed]
        if missing:
            raise MissingPrerequisite(missing)

    def _has_room_for_seat(self, s: Student) -> bool:
        return len(s.enrolled) < self._max

    # ---- helpers ----
    def _course(self, cid: str) -> Course:
        c = self._courses.get(cid)
        if c is None:
            raise UnknownCourse(cid)
        return c

    def _student(self, sid: str) -> Student:
        return self._students.setdefault(sid, Student(sid))

    def add_course(self, course_id: str, capacity: int, prerequisites: list[str]) -> None:
        with self._lock:
            if capacity < 1:
                raise InvalidCapacity(capacity)
            for p in prerequisites:
                self._course(p)
            if course_id in self._courses:
                raise DuplicateCourse(course_id)
            self._courses[course_id] = Course(course_id, capacity, list(prerequisites))

    def complete(self, student: str, course_id: str) -> None:
        with self._lock:
            self._course(course_id)
            self._student(student).completed.add(course_id)

    def enroll(self, student: str, course_id: str) -> EnrollmentStatus:
        with self._lock:
            c = self._course(course_id)
            s = self._student(student)
            for rule in self._rules:
                rule(s, c)
            if len(c.enrolled) < c.capacity:
                if not self._has_room_for_seat(s):
                    raise TooManyCourses(student)
                c.enrolled.add(s.id)
                s.enrolled.add(c.id)
                return EnrollmentStatus.ENROLLED
            c.waiting.append(s.id)
            return EnrollmentStatus.WAITLISTED

    def drop(self, student: str, course_id: str) -> None:
        with self._lock:
            c = self._course(course_id)
            s = self._student(student)
            if s.id in c.enrolled:
                c.enrolled.discard(s.id)
                s.enrolled.discard(c.id)
                self._promote(c)
            elif s.id in c.waiting:
                c.waiting.remove(s.id)
            else:
                raise NotRegistered(course_id)

    def _promote(self, c: Course) -> None:
        for sid in list(c.waiting):
            if len(c.enrolled) >= c.capacity:
                return
            s = self._student(sid)
            if self._has_room_for_seat(s):
                c.waiting.remove(sid)
                c.enrolled.add(sid)
                s.enrolled.add(c.id)

    def roster(self, course_id: str) -> list[str]:
        with self._lock:
            return sorted(self._course(course_id).enrolled)

    def waitlist(self, course_id: str) -> list[str]:
        with self._lock:
            return list(self._course(course_id).waiting)
