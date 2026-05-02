import os

from contextlib import suppress

from chart.constants import NOTATION_INDEX_TABLE
from player.pattern import NoteContainer
from player.utils import FlagBoolean, wait_until_or_cancel
from shared.utils import AUDIO_DIR

from playsound import playsound


def handler(
    note_container: NoteContainer, cancel_flag: FlagBoolean, begin_time: float
) -> None:
    status = wait_until_or_cancel(note_container.play_time + begin_time, cancel_flag)
    if status:
        # print(f"Playing note: {note_container.note} at time {note_container.play_time:.2f}")
        basename = note_container.note.token + ".mp3"
        audio_path = os.path.join(AUDIO_DIR, basename)
        with suppress(
            UnicodeDecodeError
        ):  # sometimes playsound raises this error inexplicably on windows. Why?
            playsound(audio_path)


def available() -> bool:
    # check file existence
    for token in NOTATION_INDEX_TABLE:
        basename = token + ".mp3"
        audio_path = os.path.join(AUDIO_DIR, basename)
        if not os.path.isfile(audio_path):
            return False
    return True


def name() -> str:
    return "Sound playing"
