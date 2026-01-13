import os

from chart.constants import NOTATION_INDEX_TABLE
from player.pattern import NoteContainer
from player.utils import FlagBoolean, wait_until_or_cancel

from playsound import playsound
from shared.utils import AUDIO_DIR


def handler(
    note_container: NoteContainer, cancel_flag: FlagBoolean, begin_time: float
) -> None:
    status = wait_until_or_cancel(note_container.play_time + begin_time, cancel_flag)
    if status:
        # print(f"Playing sound for note: {note_container.note}")
        basename = note_container.note.token + ".mp3"
        audio_path = os.path.join(AUDIO_DIR, basename)
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
    return "音频播放"

