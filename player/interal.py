from typing import Literal


class InternalProperty:
    """A class for internal properties used in the player runtime.
    Attributes:
    bpm: The beats per minute of the chart.
    time_signature: The time signature of the chart. Can be 3 or 4. Which represents 3/4 or 4/4 time signature.
    """

    bpm: float = 120.0  # Default BPM
    time_signature: Literal[3, 4] = 4  # Default time signature (4/4)

    def __init__(self, bpm: float = 120.0, time_signature: Literal[3, 4] = 4) -> None:
        self.bpm = bpm
        self.time_signature = time_signature

    def copy(self) -> "InternalProperty":
        """Create a copy of the InternalProperty instance."""
        return InternalProperty(bpm=self.bpm, time_signature=self.time_signature)