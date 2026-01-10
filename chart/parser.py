from chart.beat import Beat, BeatParseError
from chart.utils import is_command_line, is_beat_line

from abc import ABC, abstractmethod


class ParseError(Exception):
    def __init__(self, message: str, position: int) -> None:
        super().__init__(message)
        self.position = position


class ParseErrorInfo:
    """
    Information about a parsing error in the chart.
    Attributes:

    line_number: The line number where the error occurred.
    position: The position in the line where the error occurred.
    message: The error message.
    """

    line_number: int
    position: int
    message: str

    def __init__(self, line_number: int, position: int, message: str) -> None:
        self.line_number = line_number
        self.position = position
        self.message = message


class ChartParseException(Exception):
    """
    Exception raised for errors that occur during chart parsing.
    Attributes:
    errors: A list of ParseErrorInfo objects representing individual parsing errors.
    """

    errors: list[ParseErrorInfo]

    def __init__(self, errors: list[ParseErrorInfo]) -> None:
        super().__init__("Multiple parsing errors occurred.")
        self.errors = errors


class Line(ABC):
    """
    An abstract base class for chart lines.

    Attributes:
    raw_text: The raw text of the line.
    """

    raw_text: str
    line_number: int | None  # available when parsing a full chart

    def __init__(self, raw_text: str) -> None:
        self.raw_text = raw_text

    @abstractmethod
    def __str__(self) -> str:
        pass

    @abstractmethod
    def __repr__(self) -> str:
        pass

    def set_line_number(self, line_number: int) -> None:
        self.line_number = line_number


class TextLine(Line):
    """A class representing a text line in the chart."""

    def __str__(self) -> str:
        return self.raw_text

    def __repr__(self) -> str:
        return f"TextLine(raw_text={self.raw_text!r})"


class BeatLine(Line):
    """A class representing a beat line in the chart."""

    beats: list[Beat]
    raw_text: str

    def __init__(self, raw_text: str) -> None:
        self.raw_text = raw_text
        self.beats = []

    def set_beats(self, beats: list[Beat]) -> None:
        self.beats = beats

    def serialize(self) -> None:
        beat_strs = self.raw_text.rstrip().split("/")
        if beat_strs[-1] == "":
            beat_strs = beat_strs[:-1]
        begin_index = 0
        beats: list[Beat] = []
        for beat_str in beat_strs:
            try:
                beat = Beat.from_string(beat_str)
                beats.append(beat)
            except BeatParseError as e:
                raise ParseError(
                    f"Error parsing beat : {e}", begin_index + e.position
                ) from e
            begin_index += len(beat_str) + 1  # +1 for the '/' character
        self.set_beats(beats)

    @staticmethod
    def from_string(beat_line_str: str) -> "BeatLine":
        beat_line = BeatLine(beat_line_str)
        beat_line.serialize()
        return beat_line
    
    def set_beat_positions(self) -> None:
        """Set the line number and position for each beat in the beat line."""
        if self.line_number is None:
            return
        begin_index = 0
        for beat in self.beats:
            beat.set_position(self.line_number, begin_index)
            begin_index += len(beat.raw_text) + 1  # +1 for the '/' character

    def __str__(self) -> str:
        return self.raw_text

    def __repr__(self) -> str:
        return f"BeatLine(raw_text={self.raw_text!r}, beats={self.beats!r})"


class CommandLine(Line):
    """A class representing a command line in the chart."""

    command: str
    args: list[str]

    def serialize(self) -> None:
        """Serialize the command line

        The command line is in the format of "@command arg1 arg2 ..."

        """

        parts = self.raw_text[1:].split(" ")
        self.command = parts[0]
        self.args = parts[1:] if len(parts) > 1 else []

    @staticmethod
    def from_string(command_line_str: str) -> "CommandLine":
        command_line = CommandLine(command_line_str)
        command_line.serialize()
        return command_line

    def __str__(self) -> str:
        return self.raw_text

    def __repr__(self) -> str:
        return f"CommandLine(raw_text={self.raw_text!r})"


def parse_line(line_str: str, line_number: int) -> Line:
    """Parse a line string into a Line object."""
    result_line: Line
    if is_command_line(line_str):
        result_line = CommandLine.from_string(line_str)
    elif is_beat_line(line_str):
        result_line = BeatLine.from_string(line_str)
    else:
        result_line = TextLine(line_str)
    result_line.set_line_number(line_number)
    return result_line


def parse_chart(chart_str: str) -> list[Line]:
    """Parse a chart string into a list of Line objects."""
    lines: list[Line] = []
    line_strs = chart_str.splitlines()
    exception_list: list[ParseErrorInfo] = []
    for line_number, line_str in enumerate(line_strs, start=1):
        try:
            line = parse_line(line_str, line_number)
            lines.append(line)
        except ParseError as e:
            exception_list.append(
                ParseErrorInfo(
                    line_number=line_number,
                    position=e.position,
                    message=str(e),
                )
            )
    if exception_list:
        raise ChartParseException(exception_list)
    return lines
