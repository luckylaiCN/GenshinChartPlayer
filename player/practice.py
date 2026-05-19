import time

from typing import Callable, Any
from contextlib import suppress

from chart.constants import KEYBOARD_INDEX_TABLE, ChartKey
from player.pattern import NoteContainer
from player.runtime import BeatContainer, FlagBoolean
from shared.mac_input import native_keyboard_backend_available, register_key_listeners
from shared.utils import CURRENT_OS, OperatingSystem

if CURRENT_OS != OperatingSystem.MACOS:
    try:
        import keyboard
    except Exception:
        keyboard = None
else:
    keyboard = None


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
    _beat_index: int = 0
    current_playing_time: float = 0.0
    current_playing_beat_index: int = 0
    note_queue: list[tuple[int, NoteContainer]] = []
    waiting_keys: list[tuple[int, ChartKey]] = []  # keys that are waiting to be pressed
    pressed_keys: list[ChartKey] = []  # keys that have been pressed, wait for release
    should_stop: FlagBoolean = FlagBoolean(False)
    hooks: list[Any] = []
    on_update_index: Callable[[int], None] | None = None
    on_stop: Callable[[], None] | None = None

    def __init__(
        self,
        beat_containers: list[BeatContainer],
        should_stop: FlagBoolean | None = None,
        on_update_index: Callable[[int], None] | None = None,
        on_stop: Callable[[], None] | None = None,
    ) -> None:
        """
        Initialize the PracticeController with beat containers and an optional stop flag.
        Args:
            beat_containers (list[BeatContainer]): A list of BeatContainer instances.
            should_stop (FlagBoolean | None): An optional FlagBoolean to signal when to stop. If None, a new FlagBoolean is created.
            on_update_index (Callable[[int], None] | None): An optional callback function that is called when the current playing beat index is updated.
            on_stop (Callable[[], None] | None): An optional callback function that is called when the practice mode stops.
        """
        self.beat_containers = beat_containers
        if should_stop is None:
            self.should_stop = FlagBoolean(False)
        else:
            self.should_stop = should_stop
        self.on_update_index = on_update_index
        self.on_stop = on_stop

    def update(self, time_slice: float = 0.5) -> None:
        end_time = self.current_playing_time + time_slice
        if self._beat_index < len(self.beat_containers):
            while (
                self._beat_index < len(self.beat_containers)
                and self.beat_containers[self._beat_index].begin_time <= end_time
            ):
                beat_container = self.beat_containers[self._beat_index]
                self.note_queue.extend(
                    [(self._beat_index, note) for note in beat_container.notes]
                )
                self._beat_index += 1
                if self.should_stop.get():
                    break

    def practice_loop(self) -> None:
        self.key_listener_register()
        while not self.should_stop.get():
            while len(self.waiting_keys) > 0:
                time.sleep(0.01)
                if self.should_stop.get():
                    break
            if (
                self._beat_index >= len(self.beat_containers)
                and len(self.note_queue) == 0
            ):
                break
            next_notes = self.get_next_notes()
            for beat_index, note in next_notes:
                if note.note.keyboard is not None:
                    self.waiting_keys.append((beat_index, note.note.keyboard))
            self.remove_note_before_time(self.current_playing_time)
        self.release_all_listeners()
        self.should_stop.modify(True)
        if self.on_stop is not None:
            self.on_stop()

    def remove_note_before_time(self, time_limit: float) -> None:
        self.note_queue = [nc for nc in self.note_queue if nc[1].play_time > time_limit]
        self._check_beat_index_update()

    def get_next_notes(self) -> list[tuple[int, NoteContainer]]:
        # get notes from queue, if empty, update first
        self.update()
        if len(self.note_queue) == 0:
            self.current_playing_time += 0.5
        else:
            min_play_time = min(nc[1].play_time for nc in self.note_queue)
            self.current_playing_time = min_play_time
        while len(self.note_queue) == 0 and self._beat_index < len(
            self.beat_containers
        ):
            if len(self.note_queue) == 0:
                self.current_playing_time += 0.5
            else:
                min_play_time = min(nc[1].play_time for nc in self.note_queue)
                self.current_playing_time = min_play_time
            if self.should_stop.get():
                return []
            self.update()

        # get all notes that should be played at current_playing_time
        if len(self.note_queue) == 0:
            return []
        notes_to_play = [
            nc for nc in self.note_queue if nc[1].play_time <= self.current_playing_time
        ]
        # remove them from the queue
        self.note_queue = [
            nc for nc in self.note_queue if nc[1].play_time > self.current_playing_time
        ]
        self._check_beat_index_update()
        return notes_to_play

    def _check_beat_index_update(self) -> None:
        min_index = min(
            [beat_index for beat_index, _ in self.waiting_keys],
            default=self.current_playing_beat_index,
        )
        if min_index != self.current_playing_beat_index:
            self.current_playing_beat_index = min_index
            if self.on_update_index is not None:
                self.on_update_index(self.current_playing_beat_index)

    def on_key_press(self, key: str) -> None:
        if key not in KEYBOARD_INDEX_TABLE:
            return
        if key in [k for _, k in self.waiting_keys]:
            if key not in self.pressed_keys:
                self.pressed_keys.append(key)
                self.waiting_keys = [
                    (beat_index, k) for beat_index, k in self.waiting_keys if k != key
                ]

    def on_key_release(self, key: str) -> None:
        if key not in KEYBOARD_INDEX_TABLE:
            return
        if key in self.pressed_keys:
            self.pressed_keys.remove(key)

    def key_listener_register(self) -> None:
        if CURRENT_OS == OperatingSystem.MACOS:
            if not native_keyboard_backend_available():
                raise RuntimeError(
                    "Keyboard-based practice mode is unavailable on this platform."
                )
            print(f"[practice] registering macOS key listeners: {KEYBOARD_INDEX_TABLE}")
            listener = register_key_listeners(
                KEYBOARD_INDEX_TABLE,
                self.on_key_press,
                self.on_key_release,
            )
            if listener is not None:
                print("[practice] macOS key listeners registered")
                self.hooks.append(listener)
            else:
                print("[practice] macOS key listeners were not created")
            return

        if keyboard is None:
            raise RuntimeError("Keyboard package is unavailable on this platform.")
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
            if hasattr(hook, "stop"):
                with suppress(Exception):
                    hook.stop()  # type: ignore[attr-defined]
            elif keyboard is not None:
                with suppress(KeyError):
                    keyboard.unhook(hook)
        self.hooks.clear()

    def __del__(self):
        self.release_all_listeners()  # Ensure listeners are released upon deletion

    def stop(self) -> None:
        self.should_stop.modify(True)

    def start(self, begin_note_index: int = 0) -> None:
        self._beat_index = begin_note_index
        self.current_playing_time = 0.0
        self.note_queue.clear()
        self.waiting_keys.clear()
        self.pressed_keys.clear()
        self.should_stop.modify(False)
        self.practice_loop()

    def register_on_update_index(self, callback: Callable[[int], None]) -> None:
        self.on_update_index = callback
