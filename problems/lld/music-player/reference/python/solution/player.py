from __future__ import annotations

from collections import deque

from contract import (DuplicatePlaylist, EmptyPlaylist, MusicPlayer, NoHistory, NothingPlaying, RepeatMode,
                      UnknownPlaylist, UnknownSong)


def next_position(index: int, length: int, mode: RepeatMode) -> int | None:
    """Playback-order policy: where the playlist goes after `index` (None = stop)."""
    if mode is RepeatMode.ONE:
        return index
    if index + 1 < length:
        return index + 1
    return 0 if mode is RepeatMode.ALL else None


class Player(MusicPlayer):
    def __init__(self):
        self._songs: set[str] = set()
        self._playlists: dict[str, list[str]] = {}
        self._mode = RepeatMode.NONE
        self._entries: list[str] = []
        self._index = 0          # playlist position (of the last playlist song played)
        self._current: str | None = None
        self._queue: deque[str] = deque()
        self._history: list[tuple[str, int]] = []  # (song, playlist position at that time)

    def add_song(self, song_id: str) -> None:
        self._songs.add(song_id)

    def create_playlist(self, name: str) -> None:
        if name in self._playlists:
            raise DuplicatePlaylist(name)
        self._playlists[name] = []

    def _playlist(self, name: str) -> list[str]:
        if name not in self._playlists:
            raise UnknownPlaylist(name)
        return self._playlists[name]

    def add_to_playlist(self, name: str, song_id: str) -> None:
        pl = self._playlist(name)
        if song_id not in self._songs:
            raise UnknownSong(song_id)
        pl.append(song_id)

    def play(self, name: str) -> str:
        pl = self._playlist(name)
        if not pl:
            raise EmptyPlaylist(name)
        self._entries, self._index = list(pl), 0
        self._queue.clear()
        self._history.clear()
        self._current = pl[0]
        return self._current

    def enqueue(self, song_id: str) -> None:
        if song_id not in self._songs:
            raise UnknownSong(song_id)
        if self._current is None:
            raise NothingPlaying()
        self._queue.append(song_id)

    def next(self) -> str:
        if self._current is None:
            raise NothingPlaying()
        self._history.append((self._current, self._index))
        if self._queue:
            self._current = self._queue.popleft()
            return self._current
        pos = next_position(self._index, len(self._entries), self._mode)
        if pos is None:
            self._current = None
            return ""
        self._index = pos
        self._current = self._entries[pos]
        return self._current

    def previous(self) -> str:
        if not self._history:
            raise NoHistory()
        self._current, self._index = self._history.pop()
        return self._current

    def set_repeat(self, mode: RepeatMode) -> None:
        self._mode = mode

    def current(self) -> str:
        if self._current is None:
            raise NothingPlaying()
        return self._current
