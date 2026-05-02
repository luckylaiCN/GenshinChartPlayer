import tkinter as tk

import customtkinter as ctk

from typing import Callable, TypedDict

from gui.theme import curr_theme
from gui.utils import get_root_widget
from gui.widgets.sidebars import (
    FileFunctionalFrame,
    PlayFunctionalFrame,
    SearchFunctionalFrame,
    FunctionalFrame,
)


class FileFrameSessionData(TypedDict):
    last_opened_path: str | None


class FunctionArea(ctk.CTkFrame):
    curr_tab: str | None
    tabs: list[str]
    buttons: dict[str, ctk.CTkButton]
    event_callback: Callable[[str | None], None] | None

    def __init__(
        self,
        tabs: list[str] | None = None,
        callback: Callable[[str | None], None] | None = None,
        master=None,
        **kwargs,
    ):
        super().__init__(master, fg_color=curr_theme.BG_SECONDARY, **kwargs)
        self.curr_tab = None
        self.event_callback = callback
        self.buttons = {}
        if tabs is not None:
            self.tabs = [tab for tab in tabs]
            self.create_widgets()
        else:
            self.tabs = []

    def register_callback(self, callback: Callable[[str | None], None]) -> None:
        self.event_callback = callback

    def create_button(self, btn_name: str):
        new_btn = ctk.CTkButton(
            self,
            text=btn_name,
            width=40,
            height=40,
            fg_color="transparent",
            text_color=curr_theme.TEXT_PRIMARY,
            hover_color=curr_theme.BG_HOVER,
            command=lambda: self.on_button_click(btn_name),
        )
        new_btn.pack(pady=10)
        self.buttons[btn_name] = new_btn

    def create_widgets(self):
        for tab in self.tabs:
            self.create_button(tab)

    def on_button_click(self, tab_name: str):
        # toggle logic
        # reset all buttons' color
        for btn in self.buttons.values():
            btn.configure(fg_color="transparent")
            btn.configure(border_width=0)
        if self.curr_tab == tab_name:
            self.curr_tab = None  # toggle off
        else:
            self.curr_tab = tab_name
            # highlight the selected button
            self.buttons[tab_name].configure(
                fg_color=curr_theme.BG_PRIMARY,
                border_width=2,
                border_color=curr_theme.HIGHLIGHT_COLOR,
            )
        if self.event_callback:
            self.event_callback(self.curr_tab)

    def _set_appearance_mode(self, mode_string: str) -> None:
        super()._set_appearance_mode(mode_string)
        for btn in self.buttons.values():
            btn.configure(
                text_color=curr_theme.TEXT_PRIMARY,
                hover_color=curr_theme.BG_HOVER,
            )


class MiddleSeparator(ctk.CTkFrame):
    def __init__(self, master=None, **kwargs):
        super().__init__(master, **kwargs)
        self.configure(width=2, fg_color=curr_theme.BORDER_COLOR)
        self.pack_propagate(False)


class RightSeparator(ctk.CTkFrame):  # right separator, can be used for resizing
    master: "SidebarFrame" # pyright: ignore[reportIncompatibleVariableOverride]

    def __init__(self, master=None, **kwargs):
        super().__init__(master, **kwargs)
        self.configure(
            width=5,
            cursor="sb_h_double_arrow",
            fg_color=curr_theme.TEXT_SECONDARY,
            height=50,
        )
        self.pack_propagate(False)
        self.bind("<ButtonPress-1>", self.on_begin_drag)
        self.bind("<B1-Motion>", self.on_drag)

    def on_begin_drag(self, event: tk.Event) -> None:
        self.start_x = event.x_root
        functional_frame = self.master.functional_frame
        if functional_frame is not None:
            self.start_width = functional_frame.internal_width

    def on_drag(self, event: tk.Event) -> None:
        delta_x = event.x_root - self.start_x
        delta_x = int(delta_x / self._get_widget_scaling())  # fuck you customtkinter!

        functional_frame = self.master.functional_frame
        root = get_root_widget(self)
        max_width = int(
            root.winfo_width() / root._get_window_scaling() / 2
        )  # half on the root

        if functional_frame is not None:
            new_width = max(100, min(self.start_width + delta_x, max_width))
            functional_frame.set_width(new_width)


class SidebarFrame(ctk.CTkFrame):
    middle_separator: MiddleSeparator | None
    functional_frames: dict[str, FunctionalFrame]
    functional_frame: FunctionalFrame | None
    right_separator: RightSeparator | None

    def __init__(self, master=None, **kwargs):
        super().__init__(master, fg_color=curr_theme.BG_SECONDARY, **kwargs)

        self.functional_frames = {}
        self.functional_frame = None
        self.right_separator = None
        self.middle_separator = None
        self.create_widgets()

    def create_widgets(self):
        # from left to right:
        # function area(vertical), separator, function frame(vertical), right separator

        self.add_functional_frame("Files", FileFunctionalFrame(master=self))
        self.add_functional_frame("Search", SearchFunctionalFrame(master=self))
        self.add_functional_frame("Player", PlayFunctionalFrame(master=self))

        self.function_area = FunctionArea(
            master=self, tabs=list(self.functional_frames.keys())
        )
        self.function_area.pack(side="left", fill="y", padx=5, pady=5)

        self.function_area.register_callback(self.on_switch_function_area)

        self.function_area.on_button_click("Files")  # default open files area

    def add_functional_frame(self, name: str, frame: FunctionalFrame):
        self.functional_frames[name] = frame

    def on_switch_function_area(self, name: str | None):
        self.show_functional_frame(name)

    def show_functional_frame(self, name: str | None):
        # remove existing middle separator if any
        if self.middle_separator is not None:
            self.middle_separator.pack_forget()
            self.middle_separator = None

        # remove current functional frame if any
        for frame in self.functional_frames.values():
            frame.pack_forget()

        # remove right separator if any
        if self.right_separator is not None:
            self.right_separator.pack_forget()
            self.right_separator = None

        if name is not None and name in self.functional_frames:
            # add middle separator
            self.middle_separator = MiddleSeparator(master=self)
            self.middle_separator.pack(side="left", fill="y", padx=5, pady=5)

            func_frame = self.functional_frames[name]
            func_frame.pack(side="left", fill="y", padx=5, pady=5)

            # add right separator
            self.right_separator = RightSeparator(master=self)
            self.right_separator.pack(side="left", padx=5, pady=5)
            self.functional_frame = func_frame
        else:
            self.functional_frame = None

    def register_open_callback(self, open_callback: Callable[[str], None]) -> None:
        file_frame = self.get_functional_frame("Files")
        if isinstance(file_frame, FileFunctionalFrame):
            file_frame.register_open_callback(open_callback)

    def get_functional_frame(self, name: str) -> FunctionalFrame | None:
        return self.functional_frames.get(name)

    def dump_session(self) -> FileFrameSessionData:
        file_frame = self.get_functional_frame("Files")
        last_opened_path: str | None = None
        if isinstance(file_frame, FileFunctionalFrame):
            last_opened_path = file_frame.target_path
        return {"last_opened_path": last_opened_path}

    def load_session(self, data: FileFrameSessionData) -> None:
        file_frame = self.get_functional_frame("Files")
        if isinstance(file_frame, FileFunctionalFrame):
            last_opened_path = data.get("last_opened_path", None)
            if last_opened_path is not None:
                file_frame.set_target_path(last_opened_path)

    def _set_appearance_mode(self, mode_string):
        super()._set_appearance_mode(mode_string)
