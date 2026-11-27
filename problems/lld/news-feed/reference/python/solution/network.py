from __future__ import annotations

import heapq
import itertools
import threading
from collections import defaultdict
from dataclasses import dataclass, field

from contract import (DuplicatePost, InvalidArgument, InvalidFollow, NotAuthor, NotFollowing, SocialNetwork,
                      UnknownPost)


@dataclass
class Post:
    id: str
    author: str
    seq: int
    likers: set[str] = field(default_factory=set)
    deleted: bool = False
    reposted_by: set[str] = field(default_factory=set)


@dataclass(frozen=True)
class Entry:
    """A timeline event: an original post or a repost of one."""
    seq: int
    post: Post


class Network(SocialNetwork):
    def __init__(self):
        self._posts: dict[str, Post] = {}
        self._timelines: defaultdict[str, list[Entry]] = defaultdict(list)  # oldest -> newest
        self._following: defaultdict[str, set[str]] = defaultdict(set)
        self._seq = itertools.count()
        self._lock = threading.Lock()

    def post(self, user: str, post_id: str) -> None:
        with self._lock:
            if post_id in self._posts:
                raise DuplicatePost(post_id)
            p = Post(post_id, user, next(self._seq))
            self._posts[post_id] = p
            self._timelines[user].append(Entry(p.seq, p))

    def follow(self, follower: str, followee: str) -> None:
        if follower == followee:
            raise InvalidFollow(follower)
        with self._lock:
            self._following[follower].add(followee)

    def unfollow(self, follower: str, followee: str) -> None:
        with self._lock:
            if followee not in self._following[follower]:
                raise NotFollowing(followee)
            self._following[follower].discard(followee)

    def feed(self, user: str, limit: int) -> list[str]:
        if limit < 1:
            raise InvalidArgument(limit)
        with self._lock:
            sources = [self._timelines[u] for u in {user} | self._following[user] if self._timelines[u]]
            # k-way merge from the newest end of each timeline
            heap = [(-tl[-1].seq, i, len(tl) - 1) for i, tl in enumerate(sources)]
            heapq.heapify(heap)
            out: list[str] = []
            seen: set[str] = set()
            while heap and len(out) < limit:
                _, i, j = heapq.heappop(heap)
                p = sources[i][j].post
                if not p.deleted and p.id not in seen:
                    seen.add(p.id)
                    out.append(p.id)
                if j > 0:
                    heapq.heappush(heap, (-sources[i][j - 1].seq, i, j - 1))
            return out

    def _live(self, post_id: str) -> Post:
        p = self._posts.get(post_id)
        if p is None or p.deleted:
            raise UnknownPost(post_id)
        return p

    def delete(self, user: str, post_id: str) -> None:
        with self._lock:
            p = self._live(post_id)
            if p.author != user:
                raise NotAuthor(post_id)
            p.deleted = True

    def repost(self, user: str, post_id: str) -> bool:
        with self._lock:
            p = self._live(post_id)
            if user in p.reposted_by:
                return False
            p.reposted_by.add(user)
            self._timelines[user].append(Entry(next(self._seq), p))
            return True

    def like(self, user: str, post_id: str) -> bool:
        with self._lock:
            p = self._live(post_id)
            if user in p.likers:
                return False
            p.likers.add(user)
            return True

    def likes(self, post_id: str) -> int:
        with self._lock:
            return len(self._live(post_id).likers)
