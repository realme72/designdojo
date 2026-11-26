from __future__ import annotations

import threading
from abc import ABC, abstractmethod

from contract import (AlreadyVoted, Clock, DuplicatePoll, InvalidChoice, InvalidPoll, NotVoted, OptionResult,
                      PollClosed, PollOpen, Polls, UnknownPoll)


class BallotPolicy(ABC):
    @abstractmethod
    def validate(self, choices: list[str], options: list[str]) -> None: ...


class SingleChoice(BallotPolicy):
    def validate(self, choices, options):
        if len(choices) != 1 or choices[0] not in options:
            raise InvalidChoice(choices)


class MultiChoice(BallotPolicy):
    def validate(self, choices, options):
        if not choices or len(set(choices)) != len(choices) or any(c not in options for c in choices):
            raise InvalidChoice(choices)


class RankedChoice(MultiChoice):
    """A ranking: same validity rules as multi-choice, but order matters."""


class Tally(ABC):
    @abstractmethod
    def counted(self, choices: list[str]) -> list[str]:
        """Which options a ballot adds a vote to in `results`."""

    @abstractmethod
    def winners(self, options: list[str], ballots: list[list[str]], counts: dict[str, int]) -> list[str]: ...


class Plurality(Tally):
    def counted(self, choices):
        return choices

    def winners(self, options, ballots, counts):
        top = max(counts.values())
        return [o for o in options if counts[o] == top]


class InstantRunoff(Tally):
    def counted(self, choices):
        return choices[:1]

    def winners(self, options, ballots, counts):
        remaining = list(options)
        while True:
            tally = {o: 0 for o in remaining}
            for b in ballots:
                first = next((c for c in b if c in tally), None)
                if first is not None:
                    tally[first] += 1
            active = sum(tally.values())
            top = max(tally.values())
            if active and top * 2 > active:
                return [o for o in remaining if tally[o] == top]
            low = min(tally.values())
            survivors = [o for o in remaining if tally[o] != low]
            if not survivors:
                return remaining
            remaining = survivors


class Poll:
    def __init__(self, options: list[str], closes_at: int, policy: BallotPolicy, tally: Tally | None = None):
        self.options = options
        self.closes_at = closes_at
        self.policy = policy
        self.tally = tally or Plurality()
        self.counts = {o: 0 for o in options}
        self.ballots: dict[str, list[str]] = {}
        self.lock = threading.Lock()


class PollService(Polls):
    def __init__(self, clock: Clock):
        self._clock = clock
        self._polls: dict[str, Poll] = {}
        self._lock = threading.Lock()

    def _poll(self, poll_id: str) -> Poll:
        with self._lock:
            p = self._polls.get(poll_id)
        if p is None:
            raise UnknownPoll(poll_id)
        return p

    def _open(self, p: Poll) -> bool:
        return self._clock.now() < p.closes_at

    def create_poll(self, poll_id: str, options: list[str], closes_at: int, multi_choice: bool) -> None:
        if len(options) < 2 or len(set(options)) != len(options) or closes_at <= self._clock.now():
            raise InvalidPoll(poll_id)
        with self._lock:
            if poll_id in self._polls:
                raise DuplicatePoll(poll_id)
            self._polls[poll_id] = Poll(list(options), closes_at, MultiChoice() if multi_choice else SingleChoice())

    def create_ranked_poll(self, poll_id: str, options: list[str], closes_at: int) -> None:
        if len(options) < 2 or len(set(options)) != len(options) or closes_at <= self._clock.now():
            raise InvalidPoll(poll_id)
        with self._lock:
            if poll_id in self._polls:
                raise DuplicatePoll(poll_id)
            self._polls[poll_id] = Poll(list(options), closes_at, RankedChoice(), InstantRunoff())

    def vote(self, poll_id: str, user: str, choices: list[str]) -> None:
        p = self._poll(poll_id)
        with p.lock:
            if not self._open(p):
                raise PollClosed(poll_id)
            if user in p.ballots:
                raise AlreadyVoted(user)
            p.policy.validate(choices, p.options)
            p.ballots[user] = list(choices)
            for c in p.tally.counted(choices):
                p.counts[c] += 1

    def retract(self, poll_id: str, user: str) -> None:
        p = self._poll(poll_id)
        with p.lock:
            if not self._open(p):
                raise PollClosed(poll_id)
            ballot = p.ballots.pop(user, None)
            if ballot is None:
                raise NotVoted(user)
            for c in p.tally.counted(ballot):
                p.counts[c] -= 1

    def results(self, poll_id: str) -> list[OptionResult]:
        p = self._poll(poll_id)
        with p.lock:
            return [OptionResult(o, p.counts[o]) for o in p.options]

    def winners(self, poll_id: str) -> list[str]:
        p = self._poll(poll_id)
        with p.lock:
            if self._open(p):
                raise PollOpen(poll_id)
            return p.tally.winners(p.options, list(p.ballots.values()), p.counts)
