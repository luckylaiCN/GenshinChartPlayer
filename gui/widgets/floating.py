import customtkinter as ctk

from gui.theme import curr_theme
from player.runtime import ChartRuntime
from chart.parser import BeatLine
from shared.settings import EDITOR_FONT_FAMILY
from shared.utils import FlagBoolean


class FloatingWidget(ctk.CTkToplevel):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.overrideredirect(True)  # Remove window decorations
        self.attributes("-topmost", True)  # Keep the window on top
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
