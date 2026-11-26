from __future__ import annotations

import itertools
import threading
from collections import defaultdict
from dataclasses import dataclass, field

from contract import (Blocked, Chat, DuplicateGroup, Forbidden, InvalidMessage, Message, NotMember, Unread,
                      UnknownGroup)


@dataclass
class Conversation:
    """Append-only log; readers keep pointers (fan-out on read)."""
    log: list[tuple[int, Message]] = field(default_factory=list)  # (global seq, message)


@dataclass
class Group:
    id: str
    members: set[str] = field(default_factory=set)
    admins: set[str] = field(default_factory=set)
    windows: defaultdict[str, list[list[int | None]]] = field(default_factory=lambda: defaultdict(list))  # [from, to)

    def visible(self, user: str, seq: int) -> bool:
        return any(a <= seq and (b is None or seq < b) for a, b in self.windows.get(user, []))


class ChatService(Chat):
    def __init__(self):
        self._seq = itertools.count(1)
        self._dms: defaultdict[frozenset, Conversation] = defaultdict(Conversation)
        self._groups: dict[str, Group] = {}
        self._group_logs: defaultdict[str, Conversation] = defaultdict(Conversation)
        self._read: defaultdict[tuple[str, str], int] = defaultdict(int)  # (user, conversation) -> last seen seq
        self._blocked: defaultdict[str, set[str]] = defaultdict(set)
        self._dm_partners: defaultdict[str, set[str]] = defaultdict(set)
        self._lock = threading.Lock()

    # ---- helpers ----
    def _append(self, conv: Conversation, sender: str, text: str) -> str:
        seq = next(self._seq)
        msg = Message(f"M{seq}", sender, text)
        conv.log.append((seq, msg))
        return msg.id

    def _group(self, gid: str) -> Group:
        g = self._groups.get(gid)
        if g is None:
            raise UnknownGroup(gid)
        return g

    def _require_admin(self, g: Group, by: str) -> None:
        if by not in g.admins:
            raise Forbidden(f"{by} is not an admin of {g.id}")

    def _visible(self, user: str, conversation: str) -> list[tuple[int, Message]]:
        kind, _, key = conversation.partition(":")
        if kind == "dm":
            return list(self._dms.get(frozenset((user, key)), Conversation()).log)
        if kind == "group" and key in self._groups:
            g = self._groups[key]
            return [(s, m) for s, m in self._group_logs[key].log if g.visible(user, s)]
        return []

    # ---- direct ----
    def send_direct(self, from_user: str, to_user: str, text: str) -> str:
        if not text or from_user == to_user:
            raise InvalidMessage("empty or self")
        with self._lock:
            if from_user in self._blocked[to_user]:
                raise Blocked(to_user)
            self._dm_partners[from_user].add(to_user)
            self._dm_partners[to_user].add(from_user)
            return self._append(self._dms[frozenset((from_user, to_user))], from_user, text)

    # ---- groups ----
    def create_group(self, group_id: str, owner: str) -> None:
        with self._lock:
            if group_id in self._groups:
                raise DuplicateGroup(group_id)
            g = Group(group_id)
            self._groups[group_id] = g
            self._join(g, owner)
            g.admins.add(owner)

    def _join(self, g: Group, user: str) -> None:
        if user not in g.members:
            g.members.add(user)
            g.windows[user].append([next(self._seq), None])

    def add_member(self, group_id: str, by: str, user: str) -> None:
        with self._lock:
            g = self._group(group_id)
            self._require_admin(g, by)
            self._join(g, user)

    def remove_member(self, group_id: str, by: str, user: str) -> None:
        with self._lock:
            g = self._group(group_id)
            self._require_admin(g, by)
            if user not in g.members:
                raise NotMember(user)
            if g.admins == {user}:
                raise Forbidden("cannot remove the last admin")
            g.members.discard(user)
            g.admins.discard(user)
            g.windows[user][-1][1] = next(self._seq)

    def promote(self, group_id: str, by: str, user: str) -> None:
        with self._lock:
            g = self._group(group_id)
            self._require_admin(g, by)
            if user not in g.members:
                raise NotMember(user)
            g.admins.add(user)

    def send_group(self, group_id: str, from_user: str, text: str) -> str:
        with self._lock:
            g = self._group(group_id)
            if from_user not in g.members:
                raise NotMember(from_user)
            if not text:
                raise InvalidMessage("empty")
            return self._append(self._group_logs[group_id], from_user, text)

    # ---- reading ----
    def messages(self, user: str, conversation: str) -> list[Message]:
        with self._lock:
            return [m for _, m in self._visible(user, conversation)]

    def _conversations(self, user: str) -> list[str]:
        convs = [f"dm:{p}" for p in self._dm_partners[user]]
        convs += [f"group:{gid}" for gid, g in self._groups.items() if user in g.windows]
        return convs

    def unread(self, user: str) -> list[Unread]:
        with self._lock:
            out = []
            for conv in sorted(self._conversations(user)):
                seen = self._read[(user, conv)]
                n = sum(1 for s, m in self._visible(user, conv) if s > seen and m.from_user != user)
                if n:
                    out.append(Unread(conv, n))
            return out

    def mark_read(self, user: str, conversation: str) -> None:
        with self._lock:
            visible = self._visible(user, conversation)
            if visible:
                self._read[(user, conversation)] = visible[-1][0]

    def block(self, user: str, other: str) -> None:
        with self._lock:
            self._blocked[user].add(other)

    def unblock(self, user: str, other: str) -> None:
        with self._lock:
            self._blocked[user].discard(other)
