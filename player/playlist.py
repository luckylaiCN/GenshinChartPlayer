import os
import random

from enum import Enum
from dataclasses import dataclass
from typing import Any


class PlayMode(Enum):
    SEQUENTIAL_LOOP = "sequential_loop"
    SINGLE_LOOP = "single_loop"
    SHUFFLE = "shuffle"


@dataclass
class PlaylistEntry:
    file_path: str
    title: str = ""

    def __post_init__(self) -> None:
        if not self.title:
            basename = os.path.basename(self.file_path)
            self.title, _ = os.path.splitext(basename)


class Playlist:
    entries: list[PlaylistEntry]
    current_index: int
    play_mode: PlayMode
    _shuffle_history: list[int]

    def __init__(
        self,
        entries: list[PlaylistEntry] | None = None,
        current_index: int = 0,
        play_mode: PlayMode = PlayMode.SEQUENTIAL_LOOP,
    ) -> None:
        self.entries = entries or []
        self.current_index = current_index
        self.play_mode = play_mode
        self._shuffle_history = []

    def add_entry(self, file_path: str) -> PlaylistEntry:
        entry = PlaylistEntry(file_path=file_path)
        self.entries.append(entry)
        return entry

    def remove_entry(self, index: int) -> None:
        if 0 <= index < len(self.entries):
            self.entries.pop(index)
            if self.current_index >= len(self.entries):
                self.current_index = max(0, len(self.entries) - 1)

    def clear(self) -> None:
        self.entries.clear()
        self.current_index = 0
        self._shuffle_history.clear()

    def move_up(self, index: int) -> None:
        if index > 0 and index < len(self.entries):
            self.entries[index], self.entries[index - 1] = (
                self.entries[index - 1],
                self.entries[index],
            )
            if self.current_index == index:
                self.current_index = index - 1
            elif self.current_index == index - 1:
                self.current_index = index

    def move_down(self, index: int) -> None:
        if 0 <= index < len(self.entries) - 1:
            self.entries[index], self.entries[index + 1] = (
                self.entries[index + 1],
                self.entries[index],
            )
            if self.current_index == index:
                self.current_index = index + 1
            elif self.current_index == index + 1:
                self.current_index = index

    def get_next_index(self) -> int:
        if not self.entries:
            return -1
        if self.play_mode == PlayMode.SINGLE_LOOP:
            return self.current_index
        elif self.play_mode == PlayMode.SHUFFLE:
            return self._next_shuffle_index()
        else:
            return (self.current_index + 1) % len(self.entries)

    def get_prev_index(self) -> int:
        if not self.entries:
            return -1
        if self.play_mode == PlayMode.SINGLE_LOOP:
            return self.current_index
        elif self.play_mode == PlayMode.SHUFFLE:
            return self._next_shuffle_index()
        else:
            return (self.current_index - 1 + len(self.entries)) % len(self.entries)

    def _next_shuffle_index(self) -> int:
        if len(self.entries) == 1:
            return 0
        available = [
            i
            for i in range(len(self.entries))
            if i not in self._shuffle_history and i != self.current_index
        ]
        if not available:
            self._shuffle_history.clear()
            available = [
                i for i in range(len(self.entries)) if i != self.current_index
            ]
        if not available:
            return self.current_index
        chosen = random.choice(available)
        self._shuffle_history.append(chosen)
        return chosen

    def set_current(self, index: int) -> None:
        if 0 <= index < len(self.entries):
            self.current_index = index

    @property
    def current_entry(self) -> PlaylistEntry | None:
        if 0 <= self.current_index < len(self.entries):
            return self.entries[self.current_index]
        return None

    @property
    def is_empty(self) -> bool:
        return len(self.entries) == 0

    def dump_configuration(self) -> dict[str, Any]:
        return {
            "entries": [
                {"file_path": e.file_path, "title": e.title} for e in self.entries
            ],
            "current_index": self.current_index,
            "play_mode": self.play_mode.value,
        }

    def load_configuration(self, data: dict[str, Any]) -> None:
        self.entries = [
            PlaylistEntry(file_path=e["file_path"], title=e.get("title", ""))
            for e in data.get("entries", [])
        ]
        self.current_index = data.get("current_index", 0)
        mode_str = data.get("play_mode", PlayMode.SEQUENTIAL_LOOP.value)
        try:
            self.play_mode = PlayMode(mode_str)
        except ValueError:
            self.play_mode = PlayMode.SEQUENTIAL_LOOP
