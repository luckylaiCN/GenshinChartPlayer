import time

from typing import Callable

from chart.parser import Line, BeatLine, CommandLine

# from chart.note import SingleNote
from player.interal import InternalProperty
from player.pattern import get_notes_pattern_in_beat, NoteContainer
from player.command import command_registry
from player.utils import FlagBoolean, wait_until_or_cancel

import threading


class BeatContainer:
    beat_id: int
    notes: list[NoteContainer]
    begin_time: float = 0.0  # in seconds

    def __init__(
        self, beat_id: int, notes: list[NoteContainer], begin_time: float = 0.0
    ) -> None:
        self.beat_id = beat_id
        self.notes = notes
        self.begin_time = begin_time


class ChartRuntime:
    """
    A class representing the runtime environment for chart playback.
    Attributes:
    internal_property: An instance of InternalProperty containing internal properties for playback.
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
        for line in self.lines:
            if isinstance(line, BeatLine):
                for beat in line.beats:
                    note_containers = get_notes_pattern_in_beat(beat, current_ip)
                    ncs: list[NoteContainer] = []
                    for nc in note_containers:
                        nc_absolute = NoteContainer(
                            note=nc.note,
                            play_time=current_time + nc.relative_play_time,
                        )
                        ncs.append(nc_absolute)
                    beat_container = BeatContainer(
                        beat_id=len(self.playlist),
                        notes=ncs,
                        begin_time=current_time,
                    )
                    self.playlist.append(beat_container)
                    beat_duration = 60.0 / current_ip.bpm
                    current_time += beat_duration
            elif isinstance(line, CommandLine):
                command_registry.execute_command(line.command, line.args, current_ip)

    def get_playlist(self) -> list[BeatContainer]:
        return self.playlist


NotePlayHandler = Callable[[NoteContainer, FlagBoolean, float], None]


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
            time.time() + 0.5 - self.beats[self.current_beat_index].begin_time
        )
        threading.Thread(target=self.play_loop).start()
        return self.begin_time
