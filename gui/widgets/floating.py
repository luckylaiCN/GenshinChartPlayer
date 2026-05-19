import customtkinter as ctk
from typing import Callable, Protocol, cast

from gui.theme.default import Color
from shared.utils import CURRENT_OS, OperatingSystem
from gui.theme import curr_theme
from player.runtime import ChartRuntime
from chart.parser import BeatLine
from shared.settings import EDITOR_FONT_FAMILY
from shared.utils import FlagBoolean

try:
    import AppKit as _AppKit
except Exception:
    _AppKit = None


class _NSColorClass(Protocol):
    def colorWithCalibratedRed_green_blue_alpha_(
        self, red: float, green: float, blue: float, alpha: float
    ) -> object: ...

    def windowBackgroundColor(self) -> object: ...


class _NSFontClass(Protocol):
    def systemFontOfSize_(self, size: int) -> object: ...


class _NSPanelAlloc(Protocol):
    def initWithContentRect_styleMask_backing_defer_(
        self, rect: object, style_mask: int, backing: int, defer: bool
    ) -> "_NativeWindowProtocol": ...


class _NSPanelClass(Protocol):
    def alloc(self) -> _NSPanelAlloc: ...


class _NSTextFieldAlloc(Protocol):
    def initWithFrame_(self, frame: object) -> object: ...


class _NSTextFieldClass(Protocol):
    def alloc(self) -> _NSTextFieldAlloc: ...


class _NSScrollViewAlloc(Protocol):
    def initWithFrame_(self, frame: object) -> object: ...


class _NSScrollViewClass(Protocol):
    def alloc(self) -> _NSScrollViewAlloc: ...


class _NSTextViewAlloc(Protocol):
    def initWithFrame_(self, frame: object) -> object: ...


class _NSTextViewClass(Protocol):
    def alloc(self) -> _NSTextViewAlloc: ...


class _NSMutableAttributedStringAlloc(Protocol):
    def initWithString_(self, text: str) -> "_NSMutableAttributedStringLike": ...


class _NSMutableAttributedStringLike(Protocol):
    def addAttribute_value_range_(self, name: object, value: object, rng: tuple[int, int]) -> None: ...


class _NSMutableAttributedStringClass(Protocol):
    def alloc(self) -> _NSMutableAttributedStringAlloc: ...


class _NSScreenRect(Protocol):
    origin: "_NSPoint"
    size: "_NSSize"


class _NSPoint(Protocol):
    x: float
    y: float


class _NSSize(Protocol):
    width: float
    height: float


class _NSScreenLike(Protocol):
    def visibleFrame(self) -> _NSScreenRect: ...


class _NSAppLike(Protocol):
    def windows(self) -> list[_NativeWindowProtocol]: ...


class _NSViewLike(Protocol):
    def addSubview_(self, view: object) -> None: ...

    def frame(self) -> _NSScreenRect: ...

    def setFrame_(self, rect: object) -> None: ...


class _NSScreenClass(Protocol):
    def mainScreen(self) -> _NSScreenLike | None: ...


class _NativeWindowProtocol(Protocol):
    def title(self) -> str: ...

    def setTitle_(self, title: str) -> None: ...

    def setFloatingPanel_(self, value: bool) -> None: ...

    def setHidesOnDeactivate_(self, value: bool) -> None: ...

    def setReleasedWhenClosed_(self, value: bool) -> None: ...

    def setLevel_(self, level: int) -> None: ...

    def setCollectionBehavior_(self, behavior: int) -> None: ...

    def setTitleVisibility_(self, visibility: int) -> None: ...

    def setTitlebarAppearsTransparent_(self, value: bool) -> None: ...

    def setMovableByWindowBackground_(self, value: bool) -> None: ...

    def setOpaque_(self, value: bool) -> None: ...

    def setBackgroundColor_(self, color: object | None) -> None: ...

    def setContentSize_(self, size: object | None) -> None: ...

    def setFrameTopLeftPoint_(self, point: object | None) -> None: ...

    def setFrameOrigin_(self, point: object | None) -> None: ...

    def orderFrontRegardless(self) -> None: ...

    def orderOut_(self, sender: object | None) -> None: ...

    def close(self) -> None: ...

    def screen(self) -> _NSScreenLike | None: ...

    def frame(self) -> _NSScreenRect: ...

    def contentView(self) -> _NSViewLike: ...


class _AppKitModuleProtocol(Protocol):
    NSApp: Callable[[], _NSAppLike]
    NSColor: _NSColorClass
    NSFont: _NSFontClass
    NSPanel: _NSPanelClass
    NSTextField: _NSTextFieldClass
    NSScrollView: _NSScrollViewClass
    NSTextView: _NSTextViewClass
    NSMutableAttributedString: _NSMutableAttributedStringClass
    NSScreen: type[_NSScreenLike]
    NSWindowStyleMaskTitled: int
    NSWindowStyleMaskClosable: int
    NSWindowStyleMaskResizable: int
    NSWindowStyleMaskUtilityWindow: int
    NSWindowStyleMaskNonactivatingPanel: int
    NSBackingStoreBuffered: int
    NSStatusWindowLevel: int
    NSWindowCollectionBehaviorCanJoinAllApplications: int
    NSWindowCollectionBehaviorCanJoinAllSpaces: int
    NSWindowCollectionBehaviorStationary: int
    NSWindowCollectionBehaviorIgnoresCycle: int
    NSWindowTitleHidden: int
    NSFontAttributeName: object
    NSForegroundColorAttributeName: object
    NSBackgroundColorAttributeName: object


def _appkit_int(name: str, default: int = 0) -> int:
    return cast(int, _appkit_attr(name, default))


def _ns_color(color_value: Color, alpha: float = 1.0):
    if isinstance(color_value, tuple):
        appearance_mode = ctk.get_appearance_mode().lower()
        color_value = color_value[1 if appearance_mode == "dark" else 0]
    if _AppKit is None:
        return None
    value = color_value.strip()
    if value.startswith("#") and len(value) in {7, 9}:
        red = int(value[1:3], 16) / 255.0
        green = int(value[3:5], 16) / 255.0
        blue = int(value[5:7], 16) / 255.0
        ns_color_class = cast(_NSColorClass, getattr(_AppKit, "NSColor", None))
        if ns_color_class is None:
            return None
        return ns_color_class.colorWithCalibratedRed_green_blue_alpha_(
            red, green, blue, alpha
        )
    ns_color_class = cast(_NSColorClass, getattr(_AppKit, "NSColor", None))
    if ns_color_class is None:
        return None
    return ns_color_class.windowBackgroundColor()


def _ns_font(size: int):
    if _AppKit is None:
        return None
    ns_font_class = cast(_NSFontClass, getattr(_AppKit, "NSFont", None))
    if ns_font_class is None:
        return None
    font_factory = getattr(ns_font_class, "monospacedSystemFontOfSize_weight_", None)
    if callable(font_factory):
        return font_factory(size, 5)
    return ns_font_class.systemFontOfSize_(size)


def _ns_make_rect(x: float, y: float, width: float, height: float):
    return getattr(_AppKit, "NSMakeRect", lambda a, b, c, d: None)(x, y, width, height)


def _ns_make_size(width: float, height: float):
    return getattr(_AppKit, "NSMakeSize", lambda a, b: None)(width, height)


def _ns_make_point(x: float, y: float):
    return getattr(_AppKit, "NSMakePoint", lambda a, b: None)(x, y)


def _appkit_attr(name: str, default: object = None) -> object:
    if _AppKit is None:
        return default
    return getattr(_AppKit, name, default)


class _NativeWindow(Protocol):
    def setTitle_(self, title: str) -> None: ...

    def setFloatingPanel_(self, value: bool) -> None: ...

    def setHidesOnDeactivate_(self, value: bool) -> None: ...

    def setReleasedWhenClosed_(self, value: bool) -> None: ...

    def setLevel_(self, level: int) -> None: ...

    def setCollectionBehavior_(self, behavior: int) -> None: ...

    def setTitleVisibility_(self, visibility: int) -> None: ...

    def setTitlebarAppearsTransparent_(self, value: bool) -> None: ...

    def setMovableByWindowBackground_(self, value: bool) -> None: ...

    def setOpaque_(self, value: bool) -> None: ...

    def setBackgroundColor_(self, color: object | None) -> None: ...

    def setContentSize_(self, size: object | None) -> None: ...

    def setFrameTopLeftPoint_(self, point: object | None) -> None: ...

    def setFrameOrigin_(self, point: object | None) -> None: ...

    def orderFrontRegardless(self) -> None: ...

    def orderOut_(self, sender: object | None) -> None: ...

    def close(self) -> None: ...

    def screen(self) -> object | None: ...

    def frame(self) -> object: ...

    def contentView(self) -> object: ...


if CURRENT_OS == OperatingSystem.MACOS and _AppKit is not None:

    class NativeFloatingWidget:
        _window: _NativeWindowProtocol | None
        _content_width: int
        _content_height: int

        def __init__(self, *args, **kwargs):
            del args, kwargs
            style_mask = (
                _appkit_int("NSWindowStyleMaskTitled")
                | _appkit_int("NSWindowStyleMaskClosable")
                | _appkit_int("NSWindowStyleMaskResizable")
                | _appkit_int("NSWindowStyleMaskUtilityWindow")
                | _appkit_int("NSWindowStyleMaskNonactivatingPanel")
            )
            self._content_width = 600
            self._content_height = 100
            ns_panel = cast(_NSPanelClass, _appkit_attr("NSPanel"))
            self._window = cast(
                _NativeWindowProtocol,
                ns_panel.alloc().initWithContentRect_styleMask_backing_defer_(  # type: ignore[attr-defined]
                    _ns_make_rect(0, 0, self._content_width, self._content_height),
                    style_mask,
                    _appkit_int("NSBackingStoreBuffered", 2),
                    False,
                ),
            )
            self._window.setTitle_("GenshinChartPlayer")
            self._window.setFloatingPanel_(True)
            self._window.setHidesOnDeactivate_(False)
            self._window.setReleasedWhenClosed_(False)
            self._window.setLevel_(_appkit_int("NSStatusWindowLevel", 3))
            self._window.setCollectionBehavior_(
                _appkit_int("NSWindowCollectionBehaviorCanJoinAllApplications")
                | _appkit_int("NSWindowCollectionBehaviorCanJoinAllSpaces")
                | _appkit_int("NSWindowCollectionBehaviorStationary")
                | _appkit_int("NSWindowCollectionBehaviorIgnoresCycle")
            )
            self._window.setTitleVisibility_(_appkit_int("NSWindowTitleHidden", 1))
            self._window.setTitlebarAppearsTransparent_(True)
            self._window.setMovableByWindowBackground_(True)
            self._window.setOpaque_(False)
            self._window.setBackgroundColor_(_ns_color(curr_theme.BG_PRIMARY))

        def _apply_window_topmost(self):
            if self._window is None:
                return
            self._window.setLevel_(_appkit_int("NSStatusWindowLevel", 3))
            self._window.setCollectionBehavior_(
                _appkit_int("NSWindowCollectionBehaviorCanJoinAllApplications")
                | _appkit_int("NSWindowCollectionBehaviorCanJoinAllSpaces")
                | _appkit_int("NSWindowCollectionBehaviorStationary")
                | _appkit_int("NSWindowCollectionBehaviorIgnoresCycle")
            )
            self._window.orderFrontRegardless()

        def geometry(self, geometry_spec: str):
            if self._window is None:
                return
            size_spec, _, position_spec = geometry_spec.partition("+")
            if "x" in size_spec:
                width_text, height_text = size_spec.split("x", 1)
                self._content_width = int(width_text)
                self._content_height = int(height_text)
                self._window.setContentSize_(
                    _ns_make_size(self._content_width, self._content_height)
                )
            if position_spec:
                parts = geometry_spec.split("+")
                if len(parts) >= 3:
                    try:
                        x_pos = int(parts[1])
                        y_pos = int(parts[2])
                        self._window.setFrameTopLeftPoint_(
                            _ns_make_point(x_pos, y_pos)
                        )
                    except Exception:
                        pass

        def center_on_screen(self):
            if self._window is None:
                return
            ns_screen_class = cast(_NSScreenClass, _appkit_attr("NSScreen"))
            screen: _NSScreenLike | None = self._window.screen() or ns_screen_class.mainScreen()
            if screen is None:
                return
            visible_frame = screen.visibleFrame()
            frame = self._window.frame()
            x = visible_frame.origin.x + (visible_frame.size.width - frame.size.width) / 2
            y = visible_frame.origin.y + (visible_frame.size.height - frame.size.height) / 2
            self._window.setFrameOrigin_(_ns_make_point(x, y))

        def deiconify(self):
            if self._window is not None:
                self._window.orderFrontRegardless()

        def withdraw(self):
            if self._window is not None:
                self._window.orderOut_(None)

        def lift(self):
            self.deiconify()

        def winfo_exists(self) -> bool:
            return self._window is not None

        def destroy(self):
            if self._window is not None:
                self._window.orderOut_(None)
                self._window = None

        def _close(self):
            self.destroy()


    class NativeFloatingChartDisplay(NativeFloatingWidget):
        chart_runtime: ChartRuntime | None = None
        curr_beat_index: int = -1
        chart_line_remap: list[int] = []
        alive: FlagBoolean = FlagBoolean(True)

        def __init__(
            self,
            runtime: ChartRuntime | None = None,
            indicator: FlagBoolean | None = None,
            *args,
            **kwargs,
        ):
            super().__init__(*args, **kwargs)
            self.chart_runtime = runtime
            ns_text_field = cast(_NSTextFieldClass, _appkit_attr("NSTextField"))
            ns_scroll_view = cast(_NSScrollViewClass, _appkit_attr("NSScrollView"))
            ns_text_view = cast(_NSTextViewClass, _appkit_attr("NSTextView"))
            assert self._window is not None
            self._content_view = cast(_NSViewLike, self._window.contentView())
            self._track_label = ns_text_field.alloc().initWithFrame_(  # type: ignore[attr-defined]
                _ns_make_rect(12, self._content_height - 28, self._content_width - 24, 18)
            )
            self._track_label.setBezeled_(False)  # type: ignore[attr-defined]
            self._track_label.setDrawsBackground_(False)  # type: ignore[attr-defined]
            self._track_label.setEditable_(False)  # type: ignore[attr-defined]
            self._track_label.setSelectable_(False)  # type: ignore[attr-defined]
            self._track_label.setTextColor_(_ns_color(curr_theme.TEXT_SECONDARY))  # type: ignore[attr-defined]
            self._track_label.setFont_(_ns_font(11))  # type: ignore[attr-defined]

            self._scroll_view = ns_scroll_view.alloc().initWithFrame_(  # type: ignore[attr-defined]
                _ns_make_rect(6, 6, self._content_width - 12, self._content_height - 36)
            )
            self._scroll_view.setBorderType_(0)  # type: ignore[attr-defined]
            self._scroll_view.setHasVerticalScroller_(True)  # type: ignore[attr-defined]
            self._scroll_view.setHasHorizontalScroller_(False)  # type: ignore[attr-defined]
            self._scroll_view.setDrawsBackground_(True)  # type: ignore[attr-defined]
            self._scroll_view.setBackgroundColor_(_ns_color(curr_theme.BG_SECONDARY))  # type: ignore[attr-defined]

            self._text_view = ns_text_view.alloc().initWithFrame_(  # type: ignore[attr-defined]
                _ns_make_rect(0, 0, self._content_width - 12, self._content_height - 36)
            )
            self._text_view.setEditable_(False)  # type: ignore[attr-defined]
            self._text_view.setSelectable_(False)  # type: ignore[attr-defined]
            self._text_view.setRichText_(True)  # type: ignore[attr-defined]
            self._text_view.setDrawsBackground_(False)  # type: ignore[attr-defined]
            self._text_view.setTextColor_(_ns_color(curr_theme.TEXT_PRIMARY))  # type: ignore[attr-defined]
            self._text_view.setFont_(_ns_font(14))  # type: ignore[attr-defined]
            self._scroll_view.setDocumentView_(self._text_view)  # type: ignore[attr-defined]

            self._content_view.addSubview_(self._track_label)  # type: ignore[attr-defined]
            self._content_view.addSubview_(self._scroll_view)  # type: ignore[attr-defined]
            self._layout_native_views()
            self._apply_window_topmost()
            if indicator is not None:
                self.alive = indicator
            self.alive.modify(True)
            self._calculate_chart_line_pair()
            self._update_display()

        def _layout_native_views(self):
            if self._window is None:
                return
            content_frame = self._content_view.frame()  # type: ignore[attr-defined]
            width = content_frame.size.width
            height = content_frame.size.height
            self._track_label.setFrame_(_ns_make_rect(12, height - 26, width - 24, 18))  # type: ignore[attr-defined]
            self._scroll_view.setFrame_(_ns_make_rect(6, 6, width - 12, height - 36))  # type: ignore[attr-defined]
            self._text_view.setFrame_(_ns_make_rect(0, 0, width - 12, height - 36))  # type: ignore[attr-defined]

        def _display_lines_info(self, context_range: int = 3) -> tuple[list[str], int | None]:
            if self.chart_runtime is None:
                return [], None
            if self.curr_beat_index < 0 or self.curr_beat_index >= len(self.chart_runtime.playlist):
                return [], None
            display_lines: list[str] = []
            curr_beat = self.chart_runtime.playlist[self.curr_beat_index]
            curr_line_no_internal = curr_beat._internal_line
            total_lines = len(self.chart_line_remap)
            curr_line = self.chart_line_remap.index(curr_line_no_internal)
            start_line = max(0, curr_line - context_range // 2)
            end_line = min(total_lines, start_line + context_range)
            for line_no in range(start_line, end_line):
                internal_line_no = self.chart_line_remap[line_no]
                line_obj = self.chart_runtime.lines[internal_line_no]
                display_lines.append(str(line_obj))
            while len(display_lines) < context_range:
                display_lines.append("")
            return display_lines, curr_line - start_line

        def _calculate_chart_line_pair(self) -> None:
            self.chart_line_remap = []
            if self.chart_runtime is None:
                return
            for line_no, line in enumerate(self.chart_runtime.lines):
                if isinstance(line, BeatLine):
                    self.chart_line_remap.append(line_no)

        def _update_display(self) -> None:
            if self._window is None:
                return
            display_lines, highlight_index = self._display_lines_info()
            if not display_lines:
                text = "\n\n"
            else:
                text = "\n".join(display_lines)
            ns_mutable_attributed_string = cast(
                _NSMutableAttributedStringClass, _appkit_attr("NSMutableAttributedString")
            )
            attributed = ns_mutable_attributed_string.alloc().initWithString_(text)
            base_range = (0, len(text))
            attributed.addAttribute_value_range_(
                _appkit_attr("NSFontAttributeName"), _ns_font(14), base_range
            )
            attributed.addAttribute_value_range_(
                _appkit_attr("NSForegroundColorAttributeName"),
                _ns_color(curr_theme.TEXT_PRIMARY),
                base_range,
            )
            if highlight_index is not None and 0 <= highlight_index < len(display_lines):
                prefix = sum(len(display_lines[index]) + 1 for index in range(highlight_index))
                line_length = len(display_lines[highlight_index])
                if line_length > 0:
                    attributed.addAttribute_value_range_(
                        _appkit_attr("NSBackgroundColorAttributeName"),
                        _ns_color(curr_theme.PLAYING_HIGHLIGHT_BG),
                        (prefix, line_length),
                    )
            self._text_view.textStorage().setAttributedString_(attributed)  # type: ignore[attr-defined]

        def set_runtime(self, runtime: ChartRuntime) -> None:
            self.chart_runtime = runtime
            self._calculate_chart_line_pair()
            self._update_display()

        def set_beat_index(self, index: int) -> None:
            self.curr_beat_index = index
            self._update_display()

        def set_playlist_track_info(self, current: str, next_title: str | None = None) -> None:
            if not current:
                self._track_label.setStringValue_("")  # type: ignore[attr-defined]
                return
            text = f"\u266b {current}"
            if next_title:
                text += f"  \u2192  {next_title}"
            self._track_label.setStringValue_(text)  # type: ignore[attr-defined]

        def auto_justify_window(self) -> None:
            if self._window is None:
                return
            line_height = 18
            desired_height = line_height * 3 + 42
            self.geometry(f"{self._content_width}x{desired_height}")

        def remove_tags(self) -> None:
            self._update_display()

        def update_instantly(self) -> None:
            self._update_display()

        def _close(self):
            self.alive.modify(False)
            self.withdraw()



class _NSWindow(Protocol):
    def title(self) -> str: ...

    def setLevel_(self, level: int) -> None: ...

    def setCollectionBehavior_(self, behavior: int) -> None: ...

    def orderFrontRegardless(self) -> None: ...


class _NSApp(Protocol):
    def windows(self) -> list[_NSWindow]: ...


class _AppKitModule(Protocol):
    NSApp: Callable[[], _NSApp]
    NSStatusWindowLevel: int
    NSWindowCollectionBehaviorCanJoinAllApplications: int
    NSWindowCollectionBehaviorCanJoinAllSpaces: int
    NSWindowCollectionBehaviorStationary: int
    NSWindowCollectionBehaviorIgnoresCycle: int


def _raise_mac_window(widget: ctk.CTkToplevel) -> None:
    if _AppKit is None or CURRENT_OS != OperatingSystem.MACOS:
        return
    appkit = cast(_AppKitModuleProtocol, _AppKit)
    window_level = appkit.NSStatusWindowLevel
    collection_behavior = (
        appkit.NSWindowCollectionBehaviorCanJoinAllApplications
        | appkit.NSWindowCollectionBehaviorCanJoinAllSpaces
        | appkit.NSWindowCollectionBehaviorStationary
        | appkit.NSWindowCollectionBehaviorIgnoresCycle
    )
    window_title = widget.wm_title()
    for window in appkit.NSApp().windows():
        if window.title() == window_title:
            window.setLevel_(window_level)
            window.setCollectionBehavior_(collection_behavior)
            window.orderFrontRegardless()
            break


class FloatingWidget(ctk.CTkToplevel):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.overrideredirect(True)  # Remove window decorations
        self._dragging_frame = ctk.CTkFrame(
            self,
            height=30,
            fg_color=curr_theme.BG_PRIMARY,
            border_color=curr_theme.BORDER_COLOR,
            border_width=1,
        )
        self._close_btn = ctk.CTkButton(
            self._dragging_frame,
            text="X",
            width=30,
            height=30,
            fg_color=curr_theme.ERROR_COLOR,
            hover_color=curr_theme.ERROR_TAG_BG,
            command=self._close,
        )
        self._close_btn.pack(side="right")

        self._dragging_frame.pack(fill="x")
        self._dragging_frame.bind("<ButtonPress-1>", self._drag_start)
        self._dragging_frame.bind("<B1-Motion>", self._drag_motion)
        self.after_idle(self._apply_window_topmost)
        if CURRENT_OS == OperatingSystem.MACOS and _AppKit is not None:
            self.title("GenshinChartPlayerFloating")

    def _apply_window_topmost(self):
        self.wm_attributes("-topmost", True)
        if CURRENT_OS == OperatingSystem.MACOS and _AppKit is not None:
            self.after_idle(lambda: _raise_mac_window(self))
        self.lift()

    def _drag_start(self, event):
        self._drag_start_x = event.x
        self._drag_start_y = event.y

    def _drag_motion(self, event):
        x = self.winfo_x() + event.x - self._drag_start_x
        y = self.winfo_y() + event.y - self._drag_start_y
        self.geometry(f"+{x}+{y}")

    def center_on_screen(self):
        self.update_idletasks()
        scaling_factor = self._get_window_scaling()
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        window_width = self.winfo_width()
        window_height = self.winfo_height()
        x = (screen_width // 2) - (window_width // 2)
        y = (screen_height // 2) - (window_height // 2)
        x = int(x * scaling_factor)
        y = int(y * scaling_factor)
        self.geometry(f"+{x}+{y}")

    def _close(self):
        self.destroy()


class FloatingChartDisplay(FloatingWidget):
    chart_runtime: ChartRuntime | None = None
    curr_beat_index: int = -1
    chart_line_remap: list[int] = []
    alive: FlagBoolean = FlagBoolean(True)

    def __init__(
        self,
        runtime: ChartRuntime | None = None,
        indicator: FlagBoolean | None = None,
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.chart_runtime = runtime
        self._track_label = ctk.CTkLabel(
            self._dragging_frame,
            text="",
            text_color=curr_theme.TEXT_SECONDARY,
            font=ctk.CTkFont(size=11),
        )
        self._track_label.pack(side="left", padx=10)
        self.display_textbox = ctk.CTkTextbox(
            self,
            # width=400,
            # height=300,
            fg_color=curr_theme.BG_SECONDARY,
            text_color=curr_theme.TEXT_PRIMARY,  # type: ignore
            font=ctk.CTkFont(family=EDITOR_FONT_FAMILY, size=14, weight="normal"),
            activate_scrollbars=False,
            state="disabled",
        )
        self.display_textbox.pack(fill="both", expand=True, padx=5, pady=5)
        self.display_textbox.configure(wrap="none")
        self.display_textbox.tag_config(
            "current_beat",
            background=self._apply_appearance_mode(curr_theme.PLAYING_HIGHLIGHT_BG),
        )
        self._calculate_chart_line_pair()
        self._update_display()
        if indicator is not None:
            self.alive = indicator
        self.alive.modify(True)

    def _set_appearance_mode(self, mode_string):
        super()._set_appearance_mode(mode_string)
        self.display_textbox.tag_config(
            "current_beat",
            background=self._apply_appearance_mode(curr_theme.PLAYING_HIGHLIGHT_BG),
        )

    def set_runtime(self, runtime: ChartRuntime) -> None:
        self.chart_runtime = runtime
        self._calculate_chart_line_pair()

    def set_beat_index(self, index: int) -> None:
        self.curr_beat_index = index
        self._update_display()

    def set_playlist_track_info(self, current: str, next_title: str | None = None) -> None:
        if not current:
            self._track_label.configure(text="")
            return
        text = f"\u266b {current}"
        if next_title:
            text += f"  \u2192  {next_title}"
        self._track_label.configure(text=text)

    def _calculate_chart_line_pair(self) -> None:
        self.chart_line_remap = []
        if self.chart_runtime is None:
            return
        for line_no, line in enumerate(self.chart_runtime.lines):
            if isinstance(line, BeatLine):
                self.chart_line_remap.append(line_no)

    def _get_display_lines_info(self, context_range=3) -> tuple[list[str], str, str]:
        if self.chart_runtime is None:
            return [], "", ""
        if self.curr_beat_index < 0 or self.curr_beat_index >= len(
            self.chart_runtime.playlist
        ):
            return [], "", ""
        display_lines: list[str] = []
        curr_beat = self.chart_runtime.playlist[self.curr_beat_index]
        curr_line_no_internal = curr_beat._internal_line
        total_lines = len(self.chart_line_remap)
        curr_line = self.chart_line_remap.index(curr_line_no_internal)
        start_line = max(0, curr_line - context_range // 2)
        end_line = min(total_lines, start_line + context_range)
        for line_no in range(start_line, end_line):
            internal_line_no = self.chart_line_remap[line_no]
            line_obj = self.chart_runtime.lines[internal_line_no]
            line_str = str(line_obj)
            display_lines.append(line_str)

        while len(display_lines) < context_range:
            display_lines.append("")

        curr_line_index_in_display = curr_line - start_line + 1

        inline_begin = curr_beat.begin_str.split(".")[-1] if curr_beat.begin_str else ""
        inline_end = curr_beat.end_str.split(".")[-1] if curr_beat.end_str else ""
        new_begin_str = f"{curr_line_index_in_display}.{inline_begin}"
        new_end_str = f"{curr_line_index_in_display}.{inline_end}"

        return display_lines, new_begin_str, new_end_str

    def _update_display(self) -> None:
        self.display_textbox.configure(state="normal")
        info = self._get_display_lines_info()
        if not any(info):
            self.display_textbox.delete("1.0", "end")
            self.display_textbox.insert("1.0", "\n\n")
            self.display_textbox.configure(state="disabled")
            return
        display_lines, begin_str, end_str = info
        lines = "\n".join(display_lines)
        self.display_textbox.delete("1.0", "end")
        self.display_textbox.insert("1.0", lines)
        # Highlight current beat
        if begin_str and end_str:
            self.display_textbox.tag_remove("current_beat", "1.0", "end")
            self.display_textbox.tag_add("current_beat", begin_str, end_str)
        self.display_textbox.configure(state="disabled")
        # self._centerize_textbox_text() # buggy, disable for now

    def _centerize_textbox_text(self) -> None:
        self.display_textbox.tag_config(
            "center",
            justify="center",
        )
        self.display_textbox.tag_add("center", "1.0", "end")

    def auto_justify_window(self) -> None:
        root = self.winfo_toplevel()

        # calculate 3 lines of text in the textbox
        if self.display_textbox is None:
            return
        info = self.display_textbox.dlineinfo("1.0")
        if info is None:
            return
        line_height = info[3]  # height of a single line
        desired_height = line_height * 3 + 42
        width = root.winfo_width()
        scaling_factor = self._get_window_scaling()
        width = int(width / scaling_factor)
        self.geometry(f"{width}x{desired_height}")

    def remove_tags(self) -> None:
        self.display_textbox.tag_remove("current_beat", "1.0", "end")

    def _close(self):
        self.alive.modify(False)
        super()._close()

    def update_instantly(self) -> None:
        self._update_display()


if CURRENT_OS == OperatingSystem.MACOS and _AppKit is not None:
    globals()["FloatingWidget"] = NativeFloatingWidget  # type: ignore[name-defined]
    globals()["FloatingChartDisplay"] = NativeFloatingChartDisplay  # type: ignore[name-defined]
