Color = str | tuple[str, str]


class DefaultTheme:
    TEXT_PRIMARY: Color = ("#0e1d28", "#CCCCCC")
    TEXT_SECONDARY: Color = ("#555555", "#888889")
    TEXT_COMMENT: Color = ("#567A0D", "#378658")
    BG_PRIMARY: Color = ("#E3E3E3", "#1F1F1F")
    BG_SECONDARY: Color = ("#F1F1F1", "#181818")
    BORDER_COLOR: Color = ("#41A7E1", "#3C3C3C")
    HIGHLIGHT_COLOR: Color = ("#0078D7", "#4FC1FF")
    ERROR_COLOR: Color = ("#FF0000", "#A63838")
    WARNING_COLOR: Color = ("#FFA500", "#FFAA33")
    BG_HOVER: Color = ("#F2F2F2", "#2A2D2E")
    ERROR_TAG_BG: Color = ("#F78A8A", "#920000")
    WARNING_TAG_BG: Color = ("#FFD580", "#C97500")
    PLAYING_HIGHLIGHT_BG: Color = ("#6FCE64", "#018416")
    BTN_PRIMARY: Color = ("#6CB3EE", "#0965C1")
    _KEYS = [
        "TEXT_PRIMARY",
        "TEXT_SECONDARY",
        "TEXT_COMMENT",
        "BG_PRIMARY",
        "BG_SECONDARY",
        "BORDER_COLOR",
        "HIGHLIGHT_COLOR",
        "ERROR_COLOR",
        "WARNING_COLOR",
        "BG_HOVER",
        "ERROR_TAG_BG",
        "WARNING_TAG_BG",
        "PLAYING_HIGHLIGHT_BG",
        "BTN_PRIMARY",
    ]
