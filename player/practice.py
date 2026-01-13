import time

import keyboard

from typing import Callable

from chart.constants import KEYBOARD_INDEX_TABLE, ChartKey
from player.pattern import NoteContainer
from player.runtime import BeatContainer, FlagBoolean


class PracticeController:
    """
    A class to control the practice mode of the chart player.
    Attributes:
    beat_containers: A list of BeatContainer instances representing the beats in the chart.
    current_beat_index: The index of the current beat being processed. Can be used to track progress.
    current_playing_time: The current playing time in seconds.
    note_queue: A list of NoteContainer instances that are queued to be played.
    waiting_keys: A list of ChartKey instances that are waiting to be pressed by the user
    pressed_keys: A list of ChartKey instances that have been pressed by the user and are waiting for release.
    should_stop: A FlagBoolean instance to signal when the practice mode should stop.
    """

    beat_containers: list[BeatContainer]
    current_beat_index: int = 0
    current_playing_time: float = 0.0
    note_queue: list[NoteContainer] = []
    waiting_keys: list[ChartKey] = []  # keys that are waiting to be pressed
    pressed_keys: list[ChartKey] = []  # keys that have been pressed, wait for release
    should_stop: FlagBoolean = FlagBoolean(False)
    hooks: list[Callable[[], None]] = []

    def __init__(
        self,
        beat_containers: list[BeatContainer],
        should_stop: FlagBoolean | None = None,
    ) -> None:
        """
        Initialize the PracticeController with beat containers and an optional stop flag.
        Args:
            beat_containers (list[BeatContainer]): A list of BeatContainer instances.
            should_stop (FlagBoolean | None): An optional FlagBoolean to signal when to stop. If None, a new FlagBoolean is created.
        """
        self.beat_containers = beat_containers
        if should_stop is None:
            self.should_stop = FlagBoolean(False)
        else:
            self.should_stop = should_stop

    def update(self, time_slice: float = 0.5) -> None:
        end_time = self.current_playing_time + time_slice
        if self.current_beat_index < len(self.beat_containers):
            while (
                self.current_beat_index < len(self.beat_containers)
                and self.beat_containers[self.current_beat_index].begin_time <= end_time
            ):
                beat_container = self.beat_containers[self.current_beat_index]
                self.note_queue.extend(beat_container.notes)
                self.current_beat_index += 1

    def partice_loop(self) -> None:
        self.key_listener_register()
        while not self.should_stop.get():
            while len(self.waiting_keys) > 0:
                time.sleep(0.01)
            if (
                self.current_beat_index >= len(self.beat_containers)
                and len(self.note_queue) == 0
            ):
                break
            next_notes = self.get_next_notes()
            for note in next_notes:
                if note.note.keyboard is not None:
                    self.waiting_keys.append(note.note.keyboard)
            self.remove_note_before_time(self.current_playing_time)
        self.release_all_listeners()

    def remove_note_before_time(self, time_limit: float) -> None:
        self.note_queue = [nc for nc in self.note_queue if nc.play_time > time_limit]

    def get_next_notes(self) -> list[NoteContainer]:
        # get notes from queue, if empty, update first
        self.update()
        if len(self.note_queue) == 0:
            self.current_playing_time += 0.5
        else:
            min_play_time = min(nc.play_time for nc in self.note_queue)
            self.current_playing_time = min_play_time
        while len(self.note_queue) == 0 and self.current_beat_index < len(
            self.beat_containers
        ):
            if len(self.note_queue) == 0:
                self.current_playing_time += 0.5
            else:
                min_play_time = min(nc.play_time for nc in self.note_queue)
                self.current_playing_time = min_play_time
            print(1)
            self.update()

        # get all notes that should be played at current_playing_time
        if len(self.note_queue) == 0:
            return []
        notes_to_play = [
            nc for nc in self.note_queue if nc.play_time <= self.current_playing_time
        ]
        # remove them from the queue
        self.note_queue = [
            nc for nc in self.note_queue if nc.play_time > self.current_playing_time
        ]
        return notes_to_play

    def on_key_press(self, key: ChartKey) -> None:
        if key in self.waiting_keys:
            if key not in self.pressed_keys:
                self.pressed_keys.append(key)
                self.waiting_keys.remove(key)

    def on_key_release(self, key: ChartKey) -> None:
        if key in self.pressed_keys:
            self.pressed_keys.remove(key)

    def key_listener_register(self) -> None:
        for key in KEYBOARD_INDEX_TABLE:
            self.hooks.append(
                keyboard.on_press_key(
                    key.lower(), lambda _, k=key: self.on_key_press(k)
                )
            )
            self.hooks.append(
                keyboard.on_release_key(
                    key.lower(), lambda _, k=key: self.on_key_release(k)
                )
            )

    def release_all_listeners(self) -> None:
        for hook in self.hooks:
            keyboard.unhook(hook)
        self.hooks.clear()

    def __del__(self):
        self.release_all_listeners() # Ensure listeners are released upon deletion
