from shared.mac_input import native_keyboard_backend_available, press_and_release
from shared.utils import CURRENT_OS, OperatingSystem

from player.pattern import NoteContainer
from player.utils import FlagBoolean, wait_until_or_cancel

if CURRENT_OS != OperatingSystem.MACOS:
    try:
        import keyboard
    except Exception:
        keyboard = None
else:
    keyboard = None


def handler(
    note_container: NoteContainer, cancel_flag: FlagBoolean, begin_time: float
) -> None:
    status = wait_until_or_cancel(note_container.play_time + begin_time, cancel_flag)
    if status:
        kb = note_container.note.keyboard
        if kb is not None:
            if CURRENT_OS == OperatingSystem.MACOS and native_keyboard_backend_available():
                press_and_release(kb.lower())
            elif keyboard is not None:
                keyboard.press_and_release(
                    kb.lower()
                )  # for single key presses, lowercase the key.


def available() -> bool:
    if CURRENT_OS == OperatingSystem.MACOS:
        return native_keyboard_backend_available()
    if keyboard is None:
        return False
    try:
        keyboard.write("")  # Test if keyboard module is functional
        return True
    except Exception:
        return False


def name() -> str:
    return "Keyboard Input"
