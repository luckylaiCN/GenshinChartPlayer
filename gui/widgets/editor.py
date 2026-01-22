import customtkinter as ctk

from typing import Callable

from player.pattern import PatternMismatchException
from player.runtime import ChartRuntime
from player.interal import InternalProperty
from chart.parser import ChartParseException, parse_chart
from player.command import CommandParseException
from gui.file_handler import FileTab
from gui.theme import curr_theme
from shared.settings import EDITOR_FONT_FAMILY


EditorExceptionType = (
    PatternMismatchException | ChartParseException | CommandParseException
)


class ErrorWarningMessage(ctk.CTkFrame):
    def __init__(self, master=None, messages: list[EditorExceptionType] = [], **kwargs):
        super().__init__(master, **kwargs)
        self.messages = messages
        self.create_widgets()

    def create_widgets(self):
        self.text_area = ctk.CTkTextbox(
            self,
            wrap="word",
            height=100,
            fg_color=curr_theme.BG_SECONDARY,
            text_color=curr_theme.TEXT_PRIMARY,  # type: ignore
        )
        self.text_area.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        self.display_messages()

    def update_messages(self, messages: list[EditorExceptionType]):
        self.messages = messages
        self.display_messages()

    def display_messages(self):
        self.text_area.configure(state="normal")
        self.text_area.delete("0.0", "end")
        for msg in self.messages:
            if isinstance(msg, PatternMismatchException):
                for detail in msg.warnings:
                    line_no_str = detail.begin_str.split(".")[0]
                    if line_no_str == "":  # should not happen
                        line_no_str = "0"
                    line_no = int(line_no_str)
                    self.text_area.insert(
                        "end",
                        f"Pattern Mismatch at line {line_no}: {detail.message}\n",
                    )
            elif isinstance(msg, ChartParseException):
                for detail in msg.errors:
                    line_no = (
                        detail.line_number
                        if detail.line_number is not None
                        else "Unknown"  # should not happen
                    )
                    self.text_area.insert(
                        "end",
                        f"Chart Parse Error at line {line_no}: {detail.message}\n",
                    )
            elif isinstance(msg, CommandParseException):
                for detail in msg.errors:
                    line_no = (
                        detail.line_number
                        if detail.line_number is not None
                        else "Unknown"  # should not happen
                    )
                    self.text_area.insert(
                        "end",
                        f"Command Parse Error at line {line_no}: {detail.message}\n",
                    )
        if not self.messages:
            self.text_area.insert("end", "All checks passed.\n")
        self.text_area.configure(state="disabled")


class ExpandableCommandFrame(
    ctk.CTkFrame
):  # A frame that can expand and collapse to show/hide its content
    def __init__(self, master=None, title="Problems", **kwargs):
        super().__init__(master, **kwargs)
        self.configure(fg_color=curr_theme.BG_SECONDARY)
        self.is_expanded = True

        self.header_frame = ctk.CTkFrame(
            self, height=30, fg_color=curr_theme.BG_SECONDARY
        )
        self.header_frame.pack(fill="x", padx=10, pady=10)

        self.toggle_button = ctk.CTkButton(
            self.header_frame,
            text=title,
            command=self.toggle,
            fg_color="transparent",
            text_color=curr_theme.TEXT_PRIMARY,
            width=20,
        )
        self.toggle_button.pack(
            side="left",
        )

        self.content_frame = ErrorWarningMessage(
            self,
            fg_color=curr_theme.BG_SECONDARY,
        )
        self.content_frame.pack(fill="x", padx=10, pady=(0, 10))

        self.toggle()  # start collapsed

    def set_messages(self, messages: list[EditorExceptionType]):
        self.content_frame.update_messages(messages)
        count = 0
        for msg in messages:
            if isinstance(msg, PatternMismatchException):
                count += len(msg.warnings)
            elif isinstance(msg, (ChartParseException, CommandParseException)):
                count += len(msg.errors)
        if count > 0:
            self.toggle_button.configure(text=f"Problems ({count})")
        else:
            self.toggle_button.configure(text="Problems")

    def toggle(self):
        if self.is_expanded:
            self.content_frame.forget()
            self.is_expanded = False
        else:
            self.content_frame.pack(fill="both", expand=True)
            self.is_expanded = True


class LineNumbers(ctk.CTkTextbox):
    line_count = 0

    def __init__(
        self, master=None, text_widget: ctk.CTkTextbox | None = None, **kwargs
    ):
        super().__init__(
            master,
            width=40,
            fg_color=curr_theme.BG_SECONDARY,
            text_color=curr_theme.TEXT_PRIMARY,  # type: ignore
            state="disabled",
            activate_scrollbars=False,
            **kwargs,
        )
        self.text_widget = text_widget
        if self.text_widget:
            self.text_widget.bind("<KeyRelease>", self.update_line_numbers)
            self.update_line_numbers()
            self.text_widget._textbox.configure(yscrollcommand=self.scroll_set_remap)
            self.text_widget.bind(
                "<ButtonRelease-1>", lambda e: self.update_insert_cursor()
            )

        self.configure(wrap="none")
        self.tag_config(
            "current_line",
            foreground=self._apply_appearance_mode(curr_theme.HIGHLIGHT_COLOR),
        )
        self.update_line_numbers()

    # def y_view_remap

    def scroll_set_remap(self, first, last):
        # original behavior
        if not self.text_widget:
            return
        self.text_widget._y_scrollbar.set(first, last)
        # remap to line numbers
        self.update_yview()

    def update_yview(self):
        if self.text_widget:
            y_view = self.text_widget.yview()
            self.yview_moveto(y_view[0])  # type: ignore

    def update_insert_cursor(self):
        if not self.text_widget:
            return
        current_line = int(self.text_widget.index("insert").split(".")[0])
        self.tag_remove("current_line", "0.0", "end")
        self.tag_add("current_line", f"{current_line}.0", f"{current_line}.0 lineend")

    def update_line_numbers(self, event=None):
        if not self.text_widget:
            return
        self.update_insert_cursor()
        line_count = int(self.text_widget.index("end-1c").split(".")[0])
        if line_count == self.line_count:
            return  # no change
        self.configure(state="normal")
        self.delete("0.0", "end")
        line_numbers_str = "\n".join(str(i) for i in range(1, line_count + 1))
        self.insert("0.0", line_numbers_str)
        self.configure(state="disabled")
        max_width = max(self._font.measure(str(line_count)), 10)  # type: ignore
        max_width = int(max_width * 2)
        self.configure(width=max_width)
        self.update_yview()
        # rjust align
        self.tag_remove("right_align", "0.0", "end")
        self.tag_config("right_align", justify="right")
        self.tag_add("right_align", "0.0", "end")
        # highlight current line number
        self.line_count = line_count


class MultipleFileTabFrame(ctk.CTkTabview):
    files: list[FileTab]
    curr_text_area: ctk.CTkTextbox | None
    text_areas: dict[str, ctk.CTkTextbox]
    on_switch_tab: Callable[[str], None] | None
    on_text_change: Callable[[], None] | None
    opened_paths: set[str]

    def __init__(
        self,
        master=None,
        on_tab_switch: Callable[[str], None] | None = None,
        on_text_change: Callable[[], None] | None = None,
        **kwargs,
    ):
        super().__init__(master, command=self.callback_handle_tab_changed, **kwargs)
        self.files = []
        self.text_areas = {}
        self.opened_paths = set()
        self.on_switch_tab = on_tab_switch
        self.on_text_change = on_text_change

    def on_close_tab(self, tab_name: str):
        tab_index = self.index(tab_name)
        auto_switch_index = (
            tab_index - 1
            if tab_index > 0
            else (1 if len(self._segmented_button._value_list) - 1 > 1 else None)
        )
        if auto_switch_index is not None:
            self.set(self._segmented_button._value_list[auto_switch_index])
        self.delete(tab_name)
        self.text_areas.pop(tab_name)
        to_delete = self._get_opened_file_by_tabname(tab_name)
        if to_delete is not None:
            if to_delete.source_path is not None:
                self.opened_paths.discard(to_delete.source_path)
        self.files = [f for f in self.files if f.tab_identifier != tab_name]
        # curr_tab = self.get()
        self.callback_handle_tab_changed()

    def add_file(self, path: str | None) -> None:
        if path is not None:
            if path in self.opened_paths:
                tab = self._get_opened_file_by_path(path)
                if tab is not None:
                    self.set(tab.tab_identifier)
                return

        self.add_file_tab(
            FileTab.from_file(path) if path is not None else FileTab.new_tab()
        )

    def _get_opened_file_by_path(self, path: str) -> FileTab | None:
        for f in self.files:
            if f.source_path == path:
                return f
        return None

    def _get_opened_file_by_tabname(self, tab_name: str) -> FileTab | None:
        for f in self.files:
            if f.tab_identifier == tab_name:
                return f
        return None

    def add_file_tab(self, file_tab: FileTab):
        tab_name = file_tab.tab_identifier
        self.add(tab_name)
        self.set(tab_name)
        if file_tab.source_path is not None:
            self.opened_paths.add(file_tab.source_path)

        # close button
        close_button = ctk.CTkButton(
            self.tab(tab_name),
            text="X",
            width=20,
            height=20,
            fg_color=curr_theme.ERROR_COLOR,
            command=lambda: self.on_close_tab(tab_name),
        )
        # place close button at top right corner
        close_button.place(relx=1.0, x=-10, y=0, anchor="ne")

        # text area
        text_area = ctk.CTkTextbox(
            self.tab(tab_name),
            wrap="word",
            fg_color=curr_theme.BG_PRIMARY,
            text_color=curr_theme.TEXT_PRIMARY,  # type: ignore
            font=(EDITOR_FONT_FAMILY, 14),
        )

        line_numbers = LineNumbers(self.tab(tab_name), text_widget=text_area)

        line_numbers.pack(side="left", fill="y", padx=(5, 0), pady=40)
        text_area.pack(side="right", fill="both", expand=True, pady=40)

        text_area.configure(undo=True, autoseparators=True, maxundo=-1)
        text_area.configure(wrap="none")
        text_area.insert("0.0", file_tab.editing_content)
        # clear undo stack, so that the initial content is not undoable
        text_area.edit_reset()

        self.files.append(file_tab)
        self.text_areas[tab_name] = text_area
        self.curr_text_area = text_area

        line_numbers.update_line_numbers()
        text_area.bind("<<Modified>>", self._on_text_modified)

    def _on_text_modified(self, event):
        text_area = event.widget
        text_area.edit_modified(False)  # reset modified flag
        if self.on_text_change is not None:
            self.on_text_change()

    def bind_on_switch_tab(self, callback: Callable[[str], None]) -> None:
        self.on_switch_tab = callback

    def bind_on_text_change(self, callback: Callable[[], None]) -> None:
        self.on_text_change = callback

    def callback_handle_tab_changed(
        self,
    ):
        current_tab = self.get()
        self.curr_text_area = self.text_areas.get(current_tab)
        if self.on_switch_tab is not None:
            self.on_switch_tab(current_tab)

    def get_text_area_str(self) -> str:
        current_tab = self.get()
        text_area = self.text_areas.get(current_tab)
        if text_area is None:
            return ""
        return text_area.get("0.0", "end-1c")

    def get_current_file_tab(self) -> FileTab | None:
        current_tab = self.get()
        return self._get_opened_file_by_tabname(current_tab)


class EditorFrame(ctk.CTkFrame):
    callback_on_tab_switch: Callable[[str], None] | None
    runtime: ChartRuntime | None = None

    def __init__(
        self, master=None, callback: Callable[[str], None] | None = None, **kwargs
    ):
        super().__init__(master, **kwargs)
        self.configure(fg_color=curr_theme.BG_SECONDARY)
        self.create_widgets()
        self.callback_on_tab_switch = callback

    def register_callback(self, callback: Callable[[str], None]) -> None:
        self.callback_on_tab_switch = callback

    def create_widgets(self):
        # use rowconfigure and columnconfigure to make the text area expand with the window
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.text_areas = MultipleFileTabFrame(
            self,
            fg_color=curr_theme.BG_SECONDARY,
            border_width=2,
            border_color=curr_theme.BORDER_COLOR,
        )
        self.text_areas.grid(row=0, column=0, sticky="nsew", padx=0, pady=10)
        self.command_frame = ExpandableCommandFrame(
            self,
            title="Errors/Warnings",
            fg_color=curr_theme.BG_SECONDARY,
        )
        self.command_frame.grid(row=1, column=0, sticky="ew", padx=0, pady=10)
        self.command_frame.content_frame.configure(height=100)
        self.bind("<Configure>", self.on_resize)
        self.text_areas.bind_on_switch_tab(self.on_tab_switch)
        self.text_areas.bind_on_text_change(self.on_text_change)

    def on_tab_switch(self, tab_name: str):
        self.parse_current_chart()
        if self.callback_on_tab_switch:
            self.callback_on_tab_switch(tab_name)

    def on_text_change(self):
        self.parse_current_chart()

    def on_resize(self, event):
        if self.command_frame.is_expanded:
            new_height = self.winfo_height() - self.command_frame.winfo_height() - 40
            self.text_areas.configure(height=new_height)
        else:
            new_height = self.winfo_height() - 20
            self.text_areas.configure(height=new_height)

    def get_text(self) -> str:
        return self.text_areas.get_text_area_str()

    def handle_open_file(self, file_tab: str | None) -> None:
        self.text_areas.add_file(file_tab)
        self.parse_current_chart()

    def parse_current_chart(self):
        current_text = self.get_text()
        self.command_frame.set_messages([])
        self.reset_tags()
        if current_text.strip() == "":
            return
        messages: list[EditorExceptionType] = []
        try:
            lines = parse_chart(current_text)
        except ChartParseException as e:
            messages.append(e)
            error_line_nos = [
                err.line_number for err in e.errors if err.line_number is not None
            ]
            self.add_error_tag_to_lines(error_line_nos)
            self.command_frame.set_messages(messages)
            # set yview to first error line
            if error_line_nos:
                first_error_line = min(error_line_nos)
                text_area = self.text_areas.curr_text_area
                if text_area is not None:
                    text_area.see(f"{first_error_line}.0")
            return

        ip = InternalProperty()
        runtime = ChartRuntime(ip, lines)
        try:
            runtime.caculate_playlist()
        except PatternMismatchException as e:
            messages.append(e)
            warning_positions = [(warn.begin_str, warn.end_str) for warn in e.warnings]
            self.add_warning_tag_to_lines(warning_positions)
            if warning_positions:
                first_warning_begin_str = warning_positions[0][0]
                text_area = self.text_areas.curr_text_area
                if text_area is not None:
                    text_area.see(f"{first_warning_begin_str}")

        except CommandParseException as e:
            messages.append(e)
            error_line_nos = [
                err.line_number for err in e.errors if err.line_number is not None
            ]
            self.add_error_tag_to_lines(error_line_nos)
            if error_line_nos:
                first_error_line = min(error_line_nos)
                text_area = self.text_areas.curr_text_area
                if text_area is not None:
                    text_area.see(f"{first_error_line}.0")

        self.runtime = runtime
        self.command_frame.set_messages(messages)

    def reset_tags(self):
        tags = ["error_tag", "warning_tag"]
        text_area = self.text_areas.curr_text_area
        if text_area is None:
            return
        for tag in tags:
            text_area.tag_remove(tag, "0.0", "end")

    def add_error_tag_to_lines(self, line_nos: list[int]):
        tag_name = "error_tag"
        text_area = self.text_areas.curr_text_area
        if text_area is None:
            return
        text_area.tag_remove(tag_name, "0.0", "end")
        text_area.tag_config(
            tag_name,
            background=self._apply_appearance_mode(curr_theme.ERROR_TAG_BG),
        )
        for line_no in line_nos:
            text_area.tag_add(tag_name, f"{line_no}.0", f"{line_no}.0 lineend")

    def add_warning_tag_to_lines(self, positions: list[tuple[str, str]]):
        tag_name = "warning_tag"
        text_area = self.text_areas.curr_text_area
        if text_area is None:
            return
        text_area.tag_remove(tag_name, "0.0", "end")
        text_area.tag_config(
            tag_name,
            background=self._apply_appearance_mode(curr_theme.WARNING_TAG_BG),
        )
        for begin_str, end_str in positions:
            text_area.tag_add(tag_name, f"{begin_str}", f"{end_str}")

    def handle_new_file(self) -> None:
        self.text_areas.add_file(None)
        self.parse_current_chart()
