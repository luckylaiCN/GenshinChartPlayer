import time
import keyboard
import threading

from player.pattern import NoteContainer
from player.utils import FlagBoolean, wait_until_or_cancel


_current_keys: set[str] = set()
_active_since: float | None = None
_timer: threading.Timer | None = None
_lock = threading.Lock()
_timer_id = 0

_TIME_EPSILON = 1e-3


def _release_all_keys() -> None:
    for key in _current_keys:
        keyboard.release(key)
    _current_keys.clear()


def _do_release_all() -> None:
    global _timer, _current_keys, _active_since
    if _timer is not None:
        _timer.cancel()
        _timer = None
    _release_all_keys()
    _active_since = None


def _timer_callback(expected_id: int) -> None:
    with _lock:
        if _timer_id == expected_id:
            _do_release_all()


def handler(
    note_container: NoteContainer, cancel_flag: FlagBoolean, begin_time: float
) -> None:
    global _current_keys, _active_since, _timer, _timer_id

    play_time = note_container.play_time
    target_time = play_time + begin_time

    kb = note_container.note.keyboard
    if kb is None:
        return

    key = kb.lower()

    prerelease_time = target_time - 0.1

    # Phase 1: wait until 0.1s before target, then pre-release old keys
    if time.time() < prerelease_time:
        if not wait_until_or_cancel(prerelease_time, cancel_flag):
            if cancel_flag.get():
                with _lock:
                    _do_release_all()
            return

        with _lock:
            if cancel_flag.get():
                _do_release_all()
                return
            if (
                _active_since is not None
                and abs(play_time - _active_since) >= _TIME_EPSILON
            ):
                _do_release_all()

    # Phase 2: wait until exact play time
    status = wait_until_or_cancel(target_time, cancel_flag)
    if not status:
        if cancel_flag.get():
            with _lock:
                _do_release_all()
        return

    # Phase 3: at exact play time
    with _lock:
        if cancel_flag.get():
            _do_release_all()
            return

        if (
            _active_since is not None
            and abs(play_time - _active_since) < _TIME_EPSILON
        ):
            if key not in _current_keys:
                keyboard.press(key)
                _current_keys.add(key)
        else:
            _release_all_keys()
            keyboard.press(key)
            _current_keys = {key}
            _active_since = play_time

        _timer_id += 1
        current_id = _timer_id
        if _timer is not None:
            _timer.cancel()
        _timer = threading.Timer(2.0, _timer_callback, args=[current_id])
        _timer.start()


def available() -> bool:
    try:
        keyboard.write("")
        return True
    except Exception:
        return False


def name() -> str:
    return "Keyboard Long Press"
