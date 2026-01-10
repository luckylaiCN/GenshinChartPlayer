from typing import Literal

from chart.constants import (
    ALLOWED_TOKENS,
    ChartNotation,
    NOTATION_INDEX_TABLE,
    KEYBOARD_INDEX_TABLE,
    ChartKey,
    BracketTokenLeft,
    BracketTokenRight,
    BracketToken,
)

def is_keyboard_key(key: str) -> bool:
    """Check if the given key is a valid keyboard key."""
    return key in KEYBOARD_INDEX_TABLE


def is_valid_token(token: str) -> bool:
    """Check if the given token is a valid chart token."""
    return token in ALLOWED_TOKENS


def is_beat_line(line: str) -> bool:
    """Check if all characters in the line are valid chart tokens."""
    return all(is_valid_token(char) for char in line)


def token_to_keyboard(token: ChartNotation) -> ChartKey | None:
    """Convert a chart token to its corresponding keyboard key."""
    if token in NOTATION_INDEX_TABLE:
        index = NOTATION_INDEX_TABLE.index(token)
        return KEYBOARD_INDEX_TABLE[index]
    return None

def keyboard_to_token(key: ChartKey) -> ChartNotation | None:
    """Convert a keyboard key to its corresponding chart token."""
    if key in KEYBOARD_INDEX_TABLE:
        index = KEYBOARD_INDEX_TABLE.index(key)
        return NOTATION_INDEX_TABLE[index]
    return None


def token_to_index(token: ChartNotation) -> int:
    """Convert a chart token to its corresponding index."""
    if token in NOTATION_INDEX_TABLE:
        return NOTATION_INDEX_TABLE.index(token)
    return -1


def is_bracket_token(token: str) -> bool:
    """Check if the given token is a bracket token."""
    ALLOWED = [
        "(",
        ")",
        "[",
        "]",
        "{",
        "}",
    ]

    return token in ALLOWED


def bracket_token_direction(token: BracketToken) -> Literal["left", "right"]:
    """Determine if the bracket token is a left or right bracket."""
    LEFT = ("(", "[", "{")
    RIGHT = (")", "]", "}")
    if token in LEFT:
        return "left"
    elif token in RIGHT:
        return "right"
    else:
        raise ValueError(f"Token {token} is not a valid bracket token.")


def matching_bracket_token(token: BracketTokenLeft) -> BracketTokenRight:
    """Get the matching right bracket token for a given left bracket token."""
    MATCHING: dict[BracketTokenLeft, BracketTokenRight] = {
        "(": ")",
        "[": "]",
        "{": "}",
    }
    return MATCHING[token]


def is_bracket_match(left: BracketTokenLeft, right: BracketTokenRight) -> bool:
    """Check if the given left and right bracket tokens match."""
    MATCHING: dict[BracketTokenLeft, BracketTokenRight] = {
        "(": ")",
        "[": "]",
        "{": "}",
    }
    return MATCHING[left] == right

def is_command_line(line: str) -> bool:
    """Check if the given line is a command line (starts with an @)."""
    return line.startswith("@")

