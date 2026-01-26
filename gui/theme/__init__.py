from typing import TypedDict

from gui.theme.default import DefaultTheme, Color

ColorJsonType = str | list[str]


class OverridedTheme(TypedDict):
    overrides: dict[str, ColorJsonType]


def json_color_to_color(color_data: ColorJsonType) -> Color:
    if isinstance(color_data, str):
        if check_valid_color_string(color_data):
            return color_data
    elif isinstance(color_data, list) and len(color_data) == 2:
        if check_valid_color_string(color_data[0]) and check_valid_color_string(
            color_data[1]
        ):
            return (color_data[0], color_data[1])

    raise ValueError(f"Invalid color data: {color_data}")


def color_to_json_color(color: Color) -> ColorJsonType:
    if isinstance(color, str):
        return color
    elif isinstance(color, tuple) and len(color) == 2:
        return [color[0], color[1]]
    else:
        raise ValueError(f"Invalid color: {color}")


def check_valid_color_string(color_str: str) -> bool:
    if color_str.startswith("#") and (len(color_str) == 7 or len(color_str) == 4):
        hex_part = color_str[1:]
        try:
            int(hex_part, 16)
            return True
        except ValueError:
            return False
    return False


class ThemedColor(DefaultTheme):
    def dump_configuration(self) -> OverridedTheme:
        overrides: dict[str, ColorJsonType] = {}
        for key in DefaultTheme._KEYS:
            if getattr(self, key) != getattr(DefaultTheme, key):
                overrides[key] = color_to_json_color(getattr(self, key))
        return {"overrides": overrides}

    def load_configuration(self, data: OverridedTheme) -> None:
        overrides = data.get("overrides", {})
        for key in DefaultTheme._KEYS:
            if key in overrides:
                setattr(self, key, json_color_to_color(overrides[key]))

    def set_color(self, key: str, color: Color) -> None:
        if isinstance(color, str):
            if not check_valid_color_string(color):
                raise ValueError(f"Invalid color string: {color}")
        elif isinstance(color, tuple) and len(color) == 2:
            if not (
                check_valid_color_string(color[0])
                and check_valid_color_string(color[1])
            ):
                raise ValueError(f"Invalid color tuple: {color}")
        else:
            raise ValueError(f"Invalid color type: {color}")
        if key not in DefaultTheme._KEYS:
            raise KeyError(f"Invalid theme color key: {key}")
        setattr(self, key, color)


curr_theme: ThemedColor = ThemedColor()
