import os

import music21
import customtkinter as ctk

from typing import Callable, TypedDict
from contextlib import suppress

from player.pattern import PatternMismatchException
from player.runtime import ChartRuntime, build_chart_runtime
from player.command import CommandParseException
from player.musicxml import convert_musicxml_stream_to_chart_str
from chart.parser import ChartParseException, parse_chart, BeatLine
from chart.utils import keyboard_chart_to_numeral
from gui.file_handler import FileTab
from gui.theme import curr_theme
from gui.widgets.toast import raise_toast
from shared.settings import EDITOR_FONT_FAMILY
from shared.utils import (
    get_operation_state,
    is_operation_free,
    OperationLockState,
    WARNING_CHARACTER,
    ERROR_CHARACTER,
    is_fake_space,
)


EditorExceptionType = (
    PatternMismatchException | ChartParseException | CommandParseException
)


class EditorSessionData(TypedDict):
    opened_files_paths: list[tuple[str, bool]]  # (path, is_modified)


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
                        f"{WARNING_CHARACTER} Pattern Mismatch at line {line_no}: {detail.message}\n",
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
                        f"{ERROR_CHARACTER} Chart Parse Error at line {line_no}: {detail.message}\n",
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
                        f"{ERROR_CHARACTER} Command Parse Error at line {line_no}: {detail.message}\n",
                    )
        if not self.messages:
            self.text_area.insert("end", "All checks passed.\n")
        self.text_area.configure(state="disabled")

    def _set_appearance_mode(self, mode_string):
        self.text_area.configure(
            text_color=curr_theme.TEXT_PRIMARY  # type: ignore
        )
        return super()._set_appearance_mode(mode_string)


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

    def _set_appearance_mode(self, mode_string):
        self.toggle_button.configure(
            text_color=curr_theme.TEXT_PRIMARY,
        )
        return super()._set_appearance_mode(mode_string)


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

    def _set_appearance_mode(self, mode_string):
        super()._set_appearance_mode(mode_string)
        self.tag_config(
            "current_line",
            foreground=self._apply_appearance_mode(curr_theme.HIGHLIGHT_COLOR),
        )
        self.configure(
            text_color=curr_theme.TEXT_PRIMARY  # type: ignore
        )

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


class NumberedTextArea(ctk.CTkTextbox):
    def __init__(self, master=None, **kwargs):
        super().__init__(master, **kwargs)

    def bind_line_numbers(self, line_numbers: LineNumbers) -> None:
        self.line_numbers = line_numbers

    def bind_close_button(self, btn: ctk.CTkButton) -> None:
        self.close_button = btn

    def _set_appearance_mode(self, mode_string):
        super()._set_appearance_mode(mode_string)
        self.configure(text_color=curr_theme.TEXT_PRIMARY)
        self.line_numbers._set_appearance_mode(mode_string)


class MultipleFileTabFrame(ctk.CTkTabview):
    files: list[FileTab]
    curr_text_area: NumberedTextArea | None = None
    text_areas: dict[str, NumberedTextArea]
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

    def on_close_tab(self, tab_name: str | None = None) -> None:
        """
        Close the tab with the given name. If no name is provided, close the current tab.
        This is called when the close button on a tab is clicked.
        The param tab_name is a design mistake, as the close button always applies to the current tab,
             but it is kept for now to avoid refactoring the close button command.
        """
        if not is_operation_free():
            if get_operation_state() == OperationLockState.PLAYING:
                raise_toast(
                    self,
                    "Cannot close tab while playing is in progress.",
                    duration=3000,
                )
                return
            if get_operation_state() == OperationLockState.PRACTICING:
                # TODO: practice mode handling.
                pass
        tab_name = self._resolve_current_tab_name(tab_name)
        if tab_name is None:
            return
        try:
            tab_index = self.index(tab_name)
        except ValueError:
            return
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

    def add_file(
        self, path: str | None, is_modified: bool = False
    ) -> bool:  # if new tab created, return True
        if path is not None:
            if path in self.opened_paths:
                tab = self._get_opened_file_by_path(path)
                if tab is not None:
                    self.set(tab.tab_identifier)
                    return False
                return False  # should not happen

        if path is not None and not os.path.isfile(path):
            return False

        unmodified_tab = self.get_unmodified_file_tabs()
        if unmodified_tab:
            tab_to_use = unmodified_tab[0]
            if path is not None:
                new_filetab = FileTab.from_file(path)
            else:
                new_filetab = FileTab.new_tab()
            self._replace_tab(tab_to_use.tab_identifier, new_filetab)
            if is_modified:
                new_filetab.is_modified = True
            return True

        new_tab = FileTab.from_file(path) if path is not None else FileTab.new_tab()
        if is_modified:
            new_tab.is_modified = True
        self.add_file_tab(new_tab)
        return True

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

    def _resolve_current_tab_name(self, tab_name: str | None) -> str | None:
        if tab_name is None:
            return self.get()

        current_tabs = set(getattr(self._segmented_button, "_value_list", []))
        if tab_name in current_tabs:
            return tab_name

        for file_tab in self.files:
            if file_tab.internal_id == tab_name:
                return file_tab.tab_identifier

        _, _, internal_id = tab_name.rpartition("_")
        if internal_id == "":
            return None

        for file_tab in self.files:
            if file_tab.internal_id == internal_id:
                return file_tab.tab_identifier
        return None

    def add_file_tab(self, file_tab: FileTab):
        tab_name = file_tab.tab_identifier
        self.add(tab_name)
        is_busy = not is_operation_free()
        if not is_busy:
            self.set(tab_name)  # don't switch if it's busy
        if file_tab.source_path is not None:
            self.opened_paths.add(file_tab.source_path)

        # close button
        close_button = ctk.CTkButton(
            self.tab(tab_name),
            text="X",
            width=20,
            height=20,
            fg_color=curr_theme.ERROR_COLOR,
            command=lambda tab_id=file_tab.internal_id: self.on_close_tab(tab_id),
        )
        # place close button at top right corner
        close_button.place(relx=1.0, x=-10, y=0, anchor="ne")
        close_button.lift()

        # text area
        text_area = NumberedTextArea(
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
        text_area.bind_line_numbers(line_numbers)
        text_area.bind_close_button(close_button)
        self.files.append(file_tab)
        self.text_areas[tab_name] = text_area
        if not is_busy:
            self.curr_text_area = text_area
            self.callback_handle_tab_changed()

        line_numbers.update_line_numbers()
        text_area.bind("<<Modified>>", self._on_text_modified)
        self.update()

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

    def _set_appearance_mode(self, mode_string):
        super()._set_appearance_mode(mode_string)
        for text_area in self.text_areas.values():
            text_area.configure(text_color=curr_theme.TEXT_PRIMARY)

    def _replace_tab(self, old_file_identifier: str, new_filetab: FileTab):
        # get current text
        old_text_area = self.text_areas.get(old_file_identifier)
        if old_text_area is None:
            return

        # new_text = new_filetab.editing_content

        # close old tab
        self.on_close_tab(old_file_identifier)
        self.add_file_tab(new_filetab)

    # query file tabs that are not modified
    def get_unmodified_file_tabs(self) -> list[FileTab]:
        unmodified_tabs = []
        for file_tab in self.files:
            curr_text_area = self.text_areas.get(file_tab.tab_identifier)
            if curr_text_area is None:
                continue
            if file_tab.is_modified:
                continue
            curr_text = curr_text_area.get("0.0", "end-1c")
            if curr_text == file_tab.editing_content:
                unmodified_tabs.append(file_tab)
        return unmodified_tabs

    def new_file_text(self, text: str, tab_name: str | None = None) -> None:
        tab_name = "Untitled" if tab_name is None else tab_name
        new_tab = FileTab.new_tab()
        new_tab.default_name = tab_name
        new_tab.editing_content = text
        new_tab.is_modified = True
        self.add_file_tab(new_tab)


class EditorFrame(ctk.CTkFrame):
    callback_on_tab_switch: Callable[[str], None] | None
    runtime: ChartRuntime | None = None
    text_areas: MultipleFileTabFrame
    command_frame: ExpandableCommandFrame
    _insert_cursor_index: int = 0
    _curr_beat_index: int = -1
    can_edit: bool = True
    _playlist_add_callback: Callable[[], None] | None = None
    TOOLBAR_HEIGHT = 30

    def __init__(
        self, master=None, callback: Callable[[str], None] | None = None, **kwargs
    ):
        super().__init__(master, **kwargs)
        self.configure(fg_color=curr_theme.BG_SECONDARY)
        self.create_widgets()
        self.callback_on_tab_switch = callback
        self._listen_insert_cursor()

    def register_playlist_add_callback(self, callback: Callable[[], None]) -> None:
        self._playlist_add_callback = callback

    def _on_cursor_move(self, target_index: int | None = None):
        if not is_operation_free():
            return
        if target_index is None:
            return
        if self.runtime is None:
            return
        # mid-search for the beat that target_index belongs to
        low = 0
        high = len(self.runtime.playlist) - 1
        beat_index = -1
        while low <= high:
            mid = (low + high) // 2
            beat = self.runtime.playlist[mid]
            start = self.get_index_from_position(beat.begin_str)
            end = self.get_index_from_position(beat.end_str)
            if start <= target_index <= end:
                # found the beat
                beat_index = mid
                break
            elif target_index < start:
                high = mid - 1
            else:
                low = mid + 1
        self._curr_beat_index = beat_index
        self.highlight_current_beat()

    def highlight_current_beat(self):
        beat_index = self._curr_beat_index
        if self.runtime is None:
            return
        if beat_index == -1:
            return
        beat = self.runtime.playlist[beat_index]
        text_area = self.text_areas.curr_text_area
        if text_area is None:
            return
        text_area.tag_remove("current_beat", "0.0", "end")
        text_area.tag_config(
            "current_beat",
            background=self._apply_appearance_mode(curr_theme.PLAYING_HIGHLIGHT_BG),
        )
        text_area.tag_add("current_beat", beat.begin_str, beat.end_str)
        text_area.see(beat.begin_str)

    def _listen_insert_cursor(self):
        text_area = self.text_areas.curr_text_area
        if text_area is None:
            pass
        else:
            current_index = self.get_index_from_position(text_area.index("insert"))
            if current_index != self._insert_cursor_index:
                self._insert_cursor_index = current_index
                self._on_cursor_move(target_index=current_index)

        self.after(100, self._listen_insert_cursor)

    def register_callback(self, callback: Callable[[str], None]) -> None:
        self.callback_on_tab_switch = callback

    def create_widgets(self):
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.toolbar = ctk.CTkFrame(
            self, fg_color=curr_theme.BG_SECONDARY, height=self.TOOLBAR_HEIGHT
        )
        self.toolbar.grid(row=0, column=0, sticky="ew", padx=0, pady=(10, 0))
        self.toolbar.grid_propagate(False)

        self.add_pl_btn = ctk.CTkButton(
            self.toolbar,
            text="+ Playlist",
            command=self._on_add_to_playlist,
            fg_color=curr_theme.BTN_PRIMARY,
            height=24,
            font=ctk.CTkFont(size=12),
        )
        self.add_pl_btn.pack(side="right", padx=5, pady=2)

        self.text_areas = MultipleFileTabFrame(
            self,
            fg_color=curr_theme.BG_SECONDARY,
            border_width=2,
            border_color=curr_theme.BORDER_COLOR,
        )
        self.text_areas.grid(row=1, column=0, sticky="nsew", padx=0, pady=10)
        self.command_frame = ExpandableCommandFrame(
            self,
            title="Errors/Warnings",
            fg_color=curr_theme.BG_SECONDARY,
        )
        self.command_frame.grid(row=2, column=0, sticky="ew", padx=0, pady=10)
        self.command_frame.content_frame.configure(height=100)
        self.bind("<Configure>", self.on_resize)
        self.text_areas.bind_on_switch_tab(self.on_tab_switch)
        self.text_areas.bind_on_text_change(self.on_text_change)
        self._apply_theme()

    def _on_add_to_playlist(self) -> None:
        if self._playlist_add_callback is not None:
            self._playlist_add_callback()

    def on_tab_switch(self, tab_name: str):
        self.parse_current_chart()
        self._recall_beat_index()
        if self.callback_on_tab_switch:
            self.callback_on_tab_switch(tab_name)

    def _recall_beat_index(self):
        text_area = self.text_areas.curr_text_area
        if text_area is None:
            return
        current_index = self.get_index_from_position(text_area.index("insert"))
        self._on_cursor_move(target_index=current_index)

    def on_text_change(self):
        self.parse_current_chart()

    def on_resize(self, event):
        reserved = self.TOOLBAR_HEIGHT + 40
        if self.command_frame.is_expanded:
            new_height = self.winfo_height() - self.command_frame.winfo_height() - reserved
            self.text_areas.configure(height=new_height)
        else:
            new_height = self.winfo_height() - reserved
            with suppress(AttributeError):
                self.text_areas.configure(height=new_height)

    def get_text(self) -> str:
        return self.text_areas.get_text_area_str()

    def handle_open_file(self, file_tab: str | None, is_modified: bool = False) -> None:
        status = self.text_areas.add_file(file_tab, is_modified=is_modified)
        if status:
            self.parse_current_chart()
        self._recall_beat_index()

    def get_current_chart_musicxml_stream(self):
        if self.runtime is None:
            return None
        tab = self.text_areas.get_current_file_tab()
        name_ext = (
            os.path.basename(tab.source_path) if tab and tab.source_path else "Untitled"
        )
        file_name, _ = os.path.splitext(name_ext)
        stream = self.runtime.get_xml_stream(file_name=file_name)
        return stream

    def get_title(self) -> str:
        tab = self.text_areas.get_current_file_tab()
        if tab is None:
            return "Untitled"
        if tab.source_path is not None:
            name_ext = (
                os.path.basename(tab.source_path)
                if tab and tab.source_path
                else "Untitled"
            )
            file_name, _ = os.path.splitext(name_ext)
            return file_name
        if tab.default_name is not None:
            return tab.default_name
        return "Untitled"

    def format_chart(self) -> None:
        # reject if playing, practicing or no tab opened
        if not is_operation_free():
            raise_toast(
                self,
                "Cannot format chart while another operation is in progress.",
                duration=3000,
                position="center",
            )
            return
        if self.text_areas.curr_text_area is None:
            raise_toast(
                self,
                "No file is opened to format.",
                duration=3000,
                position="center",
            )
            return
        self.parse_current_chart(do_formatting=True)

    def remove_fake_spaces(self):

        curr_text = self.get_text()
        chars = []
        for char in curr_text:
            if is_fake_space(char):
                chars.append(" ")
            else:
                chars.append(char)
        new_text = "".join(chars)

        text_area = self.text_areas.curr_text_area
        if text_area is None:
            return

        curr_index = text_area.index("insert")
        text_area.delete("0.0", "end")
        text_area.insert("0.0", new_text)
        text_area.mark_set("insert", curr_index)
        text_area.edit_modified(False)

        self.parse_current_chart()

    def parse_current_chart(self, do_formatting: bool = False) -> None:
        self.runtime = None
        current_text = self.get_text()
        self.command_frame.set_messages([])
        self.reset_tags()
        secondary_lines: list[int] = []
        comments_str: list[tuple[str, str]] = []
        if current_text.strip() == "":
            return
        self.highlight_fake_space()
        messages: list[EditorExceptionType] = []
        try:
            lines = parse_chart(current_text, do_formatting=do_formatting)
            if do_formatting:
                # re-insert formatted text
                text_area = self.text_areas.curr_text_area
                if text_area is not None:
                    formatted_text = "\n".join(str(line) for line in lines).rstrip()
                    curr_index = text_area.index("insert")
                    text_area.delete("0.0", "end")
                    text_area.insert("0.0", formatted_text)
                    text_area.mark_set("insert", curr_index)
                    # supress <<Modified>> event
                    text_area.edit_modified(False)
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

        for idx, line in enumerate(lines):
            if isinstance(line, BeatLine):
                if line.comment_begin_index is not None:
                    begin_str = f"{idx + 1}.{line.comment_begin_index}"
                    end_str = f"{idx + 1}.end"
                    comments_str.append((begin_str, end_str))
            else:
                secondary_lines.append(idx)

        self.set_secondary_line_tags(secondary_lines)
        self.set_comment_tags(comments_str)

        runtime: ChartRuntime | None = None
        try:
            runtime = build_chart_runtime(lines)
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
        tags = [
            "error_tag",
            "warning_tag",
            "secondary_line",
            "comment_tag",
            "fake_space",
        ]
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

    def set_secondary_line_tags(self, line_nos: list[int]):
        tag_name = "secondary_line"
        text_area = self.text_areas.curr_text_area
        if text_area is None:
            return
        text_area.tag_remove(tag_name, "0.0", "end")
        text_area.tag_config(
            tag_name,
            foreground=self._apply_appearance_mode(curr_theme.TEXT_SECONDARY),
        )
        for idx in line_nos:
            line_no = idx + 1  # line numbers are 1-based
            text_area.tag_add(tag_name, f"{line_no}.0", f"{line_no}.0 lineend")

    def set_comment_tags(self, comments: list[tuple[str, str]]):
        tag_name = "comment_tag"
        text_area = self.text_areas.curr_text_area
        if text_area is None:
            return
        text_area.tag_remove(tag_name, "0.0", "end")
        text_area.tag_config(
            tag_name,
            foreground=self._apply_appearance_mode(curr_theme.TEXT_COMMENT),
        )
        for begin_str, end_str in comments:
            text_area.tag_add(tag_name, f"{begin_str}", f"{end_str}")

    def highlight_fake_space(self):
        tag_name = "fake_space"
        text_area = self.text_areas.curr_text_area
        if text_area is None:
            return
        text_area.tag_remove(tag_name, "0.0", "end")
        text_area.tag_config(
            tag_name, background=self._apply_appearance_mode(curr_theme.WARNING_TAG_BG)
        )
        curr_text = self.get_text()
        for index, char in enumerate(curr_text):
            if is_fake_space(char):
                text_area.tag_add(tag_name, f"0.0+{index}c", f"0.0+{index + 1}c")

    def handle_new_file(self) -> None:
        self.text_areas.add_file(None)
        self.parse_current_chart()

    def get_index_from_position(self, postion: str) -> int:
        """Convert a position string like '10.5' to a integer index in the text area."""
        text_area = self.text_areas.curr_text_area
        if text_area is None:
            return -1
        try:
            return int(text_area._textbox.count("0.0", postion)[0])  # type: ignore
        except Exception:
            return -1

    def get_position_from_index(self, index: int) -> str:
        """Convert a integer index in the text area to a position string like '10.5'."""
        text_area = self.text_areas.curr_text_area
        if text_area is None:
            return "0.0"
        return text_area._textbox.index(f"0.0+{index}c")  # type: ignore

    def set_current_beat_index(self, index: int) -> None:
        self._curr_beat_index = index
        self.highlight_current_beat()

    def _set_appearance_mode(self, mode_string: str) -> None:
        super()._set_appearance_mode(mode_string)
        self._apply_theme()
        self.text_areas._segmented_button.configure(
            text_color=curr_theme.TEXT_PRIMARY,
        )
        self.toolbar.configure(fg_color=curr_theme.BG_SECONDARY)
        self.add_pl_btn.configure(fg_color=curr_theme.BTN_PRIMARY)

    def _apply_theme(self) -> None:
        self.configure(fg_color=curr_theme.BG_SECONDARY)
        text_area = self.text_areas.curr_text_area
        if text_area is None:
            return
        text_area.tag_config(
            "current_beat",
            background=self._apply_appearance_mode(curr_theme.PLAYING_HIGHLIGHT_BG),
        )
        text_area.tag_config(
            "error_tag",
            background=self._apply_appearance_mode(curr_theme.ERROR_TAG_BG),
        )
        text_area.tag_config(
            "warning_tag",
            background=self._apply_appearance_mode(curr_theme.WARNING_TAG_BG),
        )
        text_area.tag_config(
            "secondary_line",
            foreground=self._apply_appearance_mode(curr_theme.TEXT_SECONDARY),
        )
        text_area.tag_config(
            "comment_tag",
            foreground=self._apply_appearance_mode(curr_theme.TEXT_COMMENT),
        )

    def modify_editable(self, can_edit: bool) -> None:
        self.can_edit = can_edit
        text_area = self.text_areas.curr_text_area
        if text_area is None:
            return
        if can_edit:
            text_area.configure(state="normal")
            self.enable_tab_switching()
        else:
            text_area.configure(state="disabled")
            self.disable_tab_switching()

    def disable_tab_switching(self) -> None:
        self.text_areas._segmented_button.configure(state="disabled")

    def enable_tab_switching(self) -> None:
        self.text_areas._segmented_button.configure(state="normal")

    def rename_tab(self, old_name: str, new_name: str) -> None:
        self.text_areas.rename(old_name, new_name)
        if old_name in self.text_areas.text_areas:
            self.text_areas.text_areas[new_name] = self.text_areas.text_areas.pop(old_name)
            if self.text_areas.curr_text_area is self.text_areas.text_areas[new_name]:
                self.text_areas.curr_text_area = self.text_areas.text_areas[new_name]
        self.text_areas.set(new_name)

    def remove_path_from_opened(self, path: str | None) -> None:
        if path is None:
            return
        if path in self.text_areas.opened_paths:
            self.text_areas.opened_paths.discard(path)

    def add_path_to_opened(self, path: str | None) -> None:
        if path is not None:
            self.text_areas.opened_paths.add(path)

    def dump_session(self) -> EditorSessionData:
        opened_files_paths: list[tuple[str, bool]] = []
        for file_tab in self.text_areas.files:
            if file_tab.source_path is not None:
                is_modified = False
                curr_text_area = self.text_areas.text_areas.get(file_tab.tab_identifier)
                if curr_text_area is not None:
                    curr_text = curr_text_area.get("0.0", "end-1c")
                    if curr_text != file_tab.editing_content:
                        is_modified = True
                if file_tab.is_modified:
                    is_modified = True
                opened_files_paths.append((file_tab.source_path, is_modified))
        return {
            "opened_files_paths": opened_files_paths,
        }

    def load_session(self, data: EditorSessionData) -> None:
        opened_files_paths = data.get("opened_files_paths", [])
        self._delay_open_files(opened_files_paths)

    def _delay_open_files(self, configs: list[tuple[str, bool]]) -> None:
        interval = 200  # milliseconds
        for i, (path, is_modified) in enumerate(configs):
            self.after(
                i * interval,
                lambda p=path, m=is_modified: self.handle_open_file(p, m),
            )

    def load_from_score(self, filepath: str) -> bool:
        basename = os.path.basename(filepath)
        name, ext = os.path.splitext(basename)
        try:
            score = music21.converter.parse(filepath)
            chart_str = convert_musicxml_stream_to_chart_str(score)
            self.text_areas.new_file_text(chart_str, tab_name=name)
            return True
        except Exception:
            return False

    def export_numeral_notation(self, filepath: str) -> bool:
        current_text = self.get_text()
        if current_text.strip() == "":
            return False
        numeral_chart_str = keyboard_chart_to_numeral(current_text)
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(numeral_chart_str)
            return True
        except Exception:
            return False
