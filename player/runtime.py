import time

import music21

from typing import Callable

from chart.parser import Line, BeatLine, CommandLine
from chart.beat import Beat

# from chart.note import SingleNote
from player.interal import InternalProperty
from player.pattern import get_notes_pattern_in_beat, NoteContainer
from player.command import (
    command_registry,
    CommandParseError,
    CommandParseErrorInfo,
    CommandParseException,
)
from player.utils import wait_until_or_cancel
from player.pattern import (
    PatternMismatchException,
    PatternMismatchWarning,
    PatternMismatchInfo,
)
from player.musicxml import (
    get_notes_partial_pattern_in_beat,
    divide_into_melody_and_chords,
)
from shared.utils import FlagBoolean

import threading


class BeatContainer:
    beat_id: int
    beat_obj: Beat
    notes: list[NoteContainer]
    begin_time: float = 0.0  # in seconds
    bpm: float = 120.0
    begin_str: str = ""
    end_str: str = ""
    _internal_line: int = -1

    def __init__(
        self,
        beat_id: int,
        beat_obj: Beat,
        notes: list[NoteContainer],
        begin_time: float = 0.0,
        bpm: float = 120.0,
        begin_str: str = "",
        end_str: str = "",
        line: int = -1,
    ) -> None:
        self.beat_id = beat_id
        self.beat_obj = beat_obj
        self.notes = notes
        self.bpm = bpm
        self.begin_time = begin_time
        self.begin_str = begin_str
        self.end_str = end_str
        self._internal_line = line


class ChartRuntime:
    """
    A class representing the runtime environment for chart playing.
    Attributes:
    internal_property: An instance of InternalProperty containing internal properties for playing.
    """

    internal_property: InternalProperty
    lines: list[Line]
    playlist: list[BeatContainer] = []

    def __init__(self, internal_property: InternalProperty, lines: list[Line]) -> None:
        self.internal_property = internal_property
        self.lines = lines

    def update_lines(self, lines: list[Line]) -> None:
        self.lines = lines
        self.caculate_playlist()

    def caculate_playlist(self) -> None:
        """Calculate the playlist based on the current lines and internal properties."""
        current_time = 0.0  # in seconds
        current_ip = self.internal_property.copy()
        warnings: list[PatternMismatchInfo] = []
        errors: list[CommandParseErrorInfo] = []
        self.playlist = []
        for index, line in enumerate(self.lines):
            line.set_line_number(index + 1)
            if isinstance(line, BeatLine):
                line.set_beat_positions()
                for beat in line.beats:
                    try:
                        note_containers = get_notes_pattern_in_beat(beat, current_ip)
                    except PatternMismatchWarning as e:
                        warning = PatternMismatchInfo(
                            message="Pattern mismatch in beat.",
                            begin_str=e.begin_str,
                            end_str=e.end_str,
                        )
                        warnings.append(warning)
                        continue
                    ncs: list[NoteContainer] = []
                    for nc in note_containers:
                        nc_absolute = NoteContainer(
                            note=nc.note,
                            play_time=current_time + nc.relative_play_time,
                        )
                        ncs.append(nc_absolute)
                    beat_container = BeatContainer(
                        beat_id=len(self.playlist),
                        beat_obj=beat,
                        notes=ncs,
                        begin_time=current_time,
                        begin_str=beat.begin_str or "",
                        end_str=beat.end_str or "",
                        bpm=current_ip.bpm,
                        line=index,
                    )
                    self.playlist.append(beat_container)
                    beat_duration = 60.0 / current_ip.bpm / current_ip.speed_multiplier
                    current_time += beat_duration
            elif isinstance(line, CommandLine):
                try:
                    command_registry.execute_command(
                        line.command, line.args, current_ip
                    )
                except CommandParseError as e:
                    error = CommandParseErrorInfo(message=str(e), line_number=index + 1)
                    errors.append(error)
        if len(errors) > 0:
            raise CommandParseException(errors)

        if len(warnings) > 0:
            raise PatternMismatchException(warnings)

        self.internal_property = current_ip

    def get_playlist(self) -> list[BeatContainer]:
        return self.playlist

    def get_xml_stream(
        self, file_name: str = "Untitled"
    ) -> music21.stream.Stream | None:
        try:
            self.caculate_playlist()  # Ensure the playlist is up to date before generating the stream
        except Exception:
            return None
        stream = music21.stream.Stream()

        

        if len(self.playlist) == 0:
            return stream
        curr_bpm = 0
        for beat_container in self.playlist:
            if beat_container.bpm != curr_bpm:
                stream.append(music21.tempo.MetronomeMark(number=beat_container.bpm))
                curr_bpm = beat_container.bpm
            beat = beat_container.beat_obj
            note_containers = get_notes_partial_pattern_in_beat(beat)
            length = len(note_containers)
            if length == 0:
                rest = music21.note.Rest()
                rest.duration.quarterLength = 1.0
                stream.append(rest)
                continue
            if note_containers[0].begin_time > 0:
                rest = music21.note.Rest()
                rest.duration.quarterLength = note_containers[0].begin_time
                stream.append(rest)
            for index, note_container in enumerate(note_containers):
                note_container.apply_to_stream(stream, index)
            if note_containers[-1].begin_time + note_containers[-1].duration < 1.0:
                rest = music21.note.Rest()
                rest.duration.quarterLength = 1.0 - (
                    note_containers[-1].begin_time + note_containers[-1].duration
                )
                stream.append(rest)

        stream = divide_into_melody_and_chords(stream, self.internal_property.time_signature)
        meta = music21.metadata.Metadata()
        meta.title = file_name
        meta.composer = self.internal_property.author
        stream.insert(0, meta)
        return stream


NotePlayHandler = Callable[
    [NoteContainer, FlagBoolean, float], None
]  # args: note_container, stop_flag, begin_time


class PlayerThreadingPool:
    stop_flag: FlagBoolean
    begin_time: float
    current_beat_index: int
    beats: list[BeatContainer]
    ADVANCE_TIME: float = 3.0
    handler: NotePlayHandler

    def __init__(self, beats: list[BeatContainer], handler: NotePlayHandler) -> None:
        self.beats = beats
        self.handler = handler
        self.stop_flag = FlagBoolean(False)
        self.begin_time = 0.0
        self.current_beat_index = 0

    def reset(self) -> None:
        self.stop_flag.modify(False)
        self.begin_time = 0.0
        self.current_beat_index = 0

    def play_loop(self):
        while self.current_beat_index < len(self.beats):
            if self.stop_flag.get():
                break
            beat_container = self.beats[self.current_beat_index]
            status = wait_until_or_cancel(
                beat_container.begin_time + self.begin_time - self.ADVANCE_TIME,
                self.stop_flag,
            )
            if status:
                threading.Thread(
                    target=self.beat_handler, args=(beat_container,)
                ).start()
            self.current_beat_index += 1

    def beat_handler(self, beat_container: BeatContainer) -> None:
        status = wait_until_or_cancel(
            beat_container.begin_time + self.begin_time - 0.5, self.stop_flag
        )
        if status:
            for note_container in beat_container.notes:
                threading.Thread(
                    target=self.handler,
                    args=(note_container, self.stop_flag, self.begin_time),
                ).start()

    def stop(self) -> None:
        self.stop_flag.modify(True)

    def play(self) -> float:  # return: the begin time
        if len(self.beats) == 0:
            return 0.0
        self.begin_time = (
            time.time() + 1 - self.beats[self.current_beat_index].begin_time
        )
        threading.Thread(target=self.play_loop).start()
        return self.begin_time

    def set_beat_index(self, index: int) -> None:
        if index < 0 or index >= len(self.beats):
            return
        self.current_beat_index = index

    def update_handler(self, handler: NotePlayHandler) -> None:
        self.handler = handler
