from typing import Literal


class InternalProperty:
    """A class for internal properties used in the player runtime.
    Attributes:
    bpm: The beats per minute of the chart.
    time_signature: The time signature of the chart. Can be 3 or 4. Which represents 3/4 or 4/4 time signature.
    """

    bpm: float = 120.0  # Default BPM
    time_signature: Literal[4] = 4  # Default time signature (4/4)
    speed_multiplier: float = 1.0  # Default speed multiplier
    author: str = "Unknown Artist"  # Default author name

    def __init__(
        self,
        bpm: float = 120.0,
        time_signature: Literal[4] = 4, # deprecated, will be removed in future versions.
        speed_multiplier: float = 1.0,
        author: str = "Unknown Artist",
    ) -> None:
        self.bpm = bpm
        self.time_signature = time_signature
        self.speed_multiplier = speed_multiplier
        self.author = author

    def set_speed_multiplier(self, multiplier: float) -> None:
        """Set the speed multiplier for the chart."""
        self.speed_multiplier = multiplier

    def copy(self) -> "InternalProperty":
        """Create a copy of the InternalProperty instance."""
        return InternalProperty(
            bpm=self.bpm,
            time_signature=self.time_signature,
            speed_multiplier=self.speed_multiplier,
            author=self.author,
        )
