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


class Poll:
    def __init__(self, options: list[str], closes_at: int, policy: BallotPolicy):
        self.options = options
        self.closes_at = closes_at
        self.policy = policy
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

    def vote(self, poll_id: str, user: str, choices: list[str]) -> None:
        p = self._poll(poll_id)
        with p.lock:
            if not self._open(p):
                raise PollClosed(poll_id)
            if user in p.ballots:
                raise AlreadyVoted(user)
            p.policy.validate(choices, p.options)
            p.ballots[user] = list(choices)
            for c in choices:
                p.counts[c] += 1

    def retract(self, poll_id: str, user: str) -> None:
        p = self._poll(poll_id)
        with p.lock:
            if not self._open(p):
                raise PollClosed(poll_id)
            ballot = p.ballots.pop(user, None)
            if ballot is None:
                raise NotVoted(user)
            for c in ballot:
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
            top = max(p.counts.values())
            return [o for o in p.options if p.counts[o] == top]
