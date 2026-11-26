from __future__ import annotations

import threading
from collections import defaultdict
from dataclasses import dataclass, field

from contract import DuplicatePost, Forbidden, InvalidQuestion, QaSite, QuestionClosed, SelfVote, UnknownPost


class StandardReputation:
    """Event -> reputation delta for the post's author. One place to change the rules."""
    QUESTION_UP, ANSWER_UP, DOWN, ACCEPTED = 5, 10, -2, 15

    def vote(self, is_answer: bool, up: bool) -> int:
        if not up:
            return self.DOWN
        return self.ANSWER_UP if is_answer else self.QUESTION_UP


@dataclass
class Post:
    id: str
    author: str
    votes: dict[str, bool] = field(default_factory=dict)  # voter -> up?

    @property
    def score(self) -> int:
        return sum(1 if up else -1 for up in self.votes.values())


@dataclass
class Question(Post):
    tags: list[str] = field(default_factory=list)
    closed: bool = False
    accepted: str | None = None


@dataclass
class Answer(Post):
    question: str = ""


class Site(QaSite):
    def __init__(self, close_threshold: int, rep: StandardReputation):
        self._close_threshold = close_threshold
        self._rep_rules = rep
        self._posts: dict[str, Post] = {}
        self._rep: defaultdict[str, int] = defaultdict(lambda: 1)
        self._lock = threading.Lock()

    def _post(self, pid: str) -> Post:
        p = self._posts.get(pid)
        if p is None:
            raise UnknownPost(pid)
        return p

    def _question(self, qid: str) -> Question:
        q = self._post(qid)
        if not isinstance(q, Question):
            raise UnknownPost(qid)
        return q

    def ask(self, user: str, question_id: str, title: str, tags: list[str]) -> None:
        if not title or not tags or len(tags) > 5:
            raise InvalidQuestion(question_id)
        with self._lock:
            if question_id in self._posts:
                raise DuplicatePost(question_id)
            self._posts[question_id] = Question(question_id, user, tags=list(tags))

    def answer(self, user: str, question_id: str, answer_id: str) -> None:
        with self._lock:
            q = self._question(question_id)
            if q.closed:
                raise QuestionClosed(question_id)
            if answer_id in self._posts:
                raise DuplicatePost(answer_id)
            self._posts[answer_id] = Answer(answer_id, user, question=question_id)

    def vote(self, user: str, post_id: str, up: bool) -> None:
        with self._lock:
            p = self._post(post_id)
            if p.author == user:
                raise SelfVote(post_id)
            old = p.votes.get(user)
            if old == up:
                return
            is_answer = isinstance(p, Answer)
            if old is not None:
                self._rep[p.author] -= self._rep_rules.vote(is_answer, old)
            p.votes[user] = up
            self._rep[p.author] += self._rep_rules.vote(is_answer, up)

    def accept(self, user: str, answer_id: str) -> None:
        with self._lock:
            a = self._post(answer_id)
            if not isinstance(a, Answer):
                raise UnknownPost(answer_id)
            q = self._question(a.question)
            if q.author != user:
                raise Forbidden("only the asker can accept")
            if q.accepted == answer_id:
                return
            if q.accepted is not None:
                prev = self._posts[q.accepted]
                if prev.author != q.author:
                    self._rep[prev.author] -= self._rep_rules.ACCEPTED
            q.accepted = answer_id
            if a.author != q.author:
                self._rep[a.author] += self._rep_rules.ACCEPTED

    def close(self, user: str, question_id: str) -> None:
        with self._lock:
            q = self._question(question_id)
            if self._rep[user] < self._close_threshold:
                raise Forbidden("not enough reputation")
            q.closed = True

    def score(self, post_id: str) -> int:
        with self._lock:
            return self._post(post_id).score

    def reputation(self, user: str) -> int:
        with self._lock:
            return self._rep[user]

    def search(self, tag: str) -> list[str]:
        with self._lock:
            qs = [p for p in self._posts.values() if isinstance(p, Question) and tag in p.tags]
            return [q.id for q in sorted(qs, key=lambda q: (-q.score, q.id))]
