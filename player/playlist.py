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
    _play_queue: list[int]
    _history_stack: list[int]
    _future_stack: list[int]

    def __init__(
        self,
        entries: list[PlaylistEntry] | None = None,
        current_index: int = 0,
        play_mode: PlayMode = PlayMode.SEQUENTIAL_LOOP,
    ) -> None:
        self.entries = entries or []
        self.current_index = current_index
        self.play_mode = play_mode
        self._play_queue = []
        self._history_stack = []
        self._future_stack = []
        self._rebuild_queue()

    def _reset_navigation_history(self) -> None:
        self._history_stack.clear()
        self._future_stack.clear()

    def _clamp_current_index(self) -> None:
        if self.entries:
            self.current_index = max(0, min(self.current_index, len(self.entries) - 1))
        else:
            self.current_index = 0

    def _rebuild_queue(self) -> None:
        self._clamp_current_index()
        if not self.entries:
            self._play_queue = []
            return

        if len(self.entries) == 1:
            self._play_queue = [self.current_index]
            return

        if self.play_mode == PlayMode.SINGLE_LOOP:
            self._play_queue = [self.current_index]
            return

        if self.play_mode == PlayMode.SHUFFLE:
            queue = [i for i in range(len(self.entries)) if i != self.current_index]
            random.shuffle(queue)
            self._play_queue = queue or [self.current_index]
            return

        self._play_queue = [
            i for i in range(self.current_index + 1, len(self.entries))
        ] + [i for i in range(0, self.current_index)]

    def _ensure_queue(self) -> None:
        if not self._play_queue:
            self._rebuild_queue()

    def _consume_next_index(self) -> int:
        if not self.entries:
            return -1
        current_before = self.current_index

        if self._future_stack:
            next_index = self._future_stack.pop()
            if current_before != next_index:
                self._history_stack.append(current_before)
            self.current_index = next_index
            self._rebuild_queue()
            return next_index

        self._ensure_queue()
        if not self._play_queue:
            return -1
        next_index = self._play_queue.pop(0)
        if current_before != next_index:
            self._history_stack.append(current_before)
        self._future_stack.clear()
        self.current_index = next_index
        if not self._play_queue:
            self._rebuild_queue()
        return next_index

    def _consume_prev_index(self) -> int:
        if not self.entries:
            return -1
        if self.play_mode == PlayMode.SINGLE_LOOP:
            return self.current_index

        current_before = self.current_index
        if self._history_stack:
            prev_index = self._history_stack.pop()
            if current_before != prev_index:
                self._future_stack.append(current_before)
            self.current_index = prev_index
            self._rebuild_queue()
            return prev_index

        prev_index = (self.current_index - 1 + len(self.entries)) % len(self.entries)
        if current_before != prev_index:
            self._future_stack.append(current_before)
        self.current_index = prev_index
        self._rebuild_queue()
        return prev_index

    def _peek_next_index(self) -> int:
        if not self.entries:
            return -1
        if self._future_stack:
            return self._future_stack[-1]
        self._ensure_queue()
        if not self._play_queue:
            return -1
        return self._play_queue[0]

    def add_entry(self, file_path: str) -> PlaylistEntry:
        entry = PlaylistEntry(file_path=file_path)
        self.entries.append(entry)
        self._reset_navigation_history()
        self._rebuild_queue()
        return entry

    def remove_entry(self, index: int) -> None:
        if 0 <= index < len(self.entries):
            self.entries.pop(index)
            if self.current_index >= len(self.entries):
                self.current_index = max(0, len(self.entries) - 1)
            self._reset_navigation_history()
            self._rebuild_queue()

    def clear(self) -> None:
        self.entries.clear()
        self.current_index = 0
        self._reset_navigation_history()
        self._play_queue.clear()

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
            self._reset_navigation_history()
            self._rebuild_queue()

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
            self._reset_navigation_history()
            self._rebuild_queue()

    def get_next_index(self) -> int:
        return self._consume_next_index()

    def peek_next_index(self) -> int:
        return self._peek_next_index()

    def get_prev_index(self) -> int:
        return self._consume_prev_index()

    def set_current(self, index: int) -> None:
        if 0 <= index < len(self.entries):
            if self.current_index == index:
                return
            self.current_index = index
            self._reset_navigation_history()
            self._rebuild_queue()

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
        self._reset_navigation_history()
        self._rebuild_queue()
