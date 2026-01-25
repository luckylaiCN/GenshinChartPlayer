import customtkinter as ctk
import keyboard
import threading

from typing import Callable, Optional

from gui.theme import curr_theme
from gui.utils import get_root_widget, translate_tkinter_bind_to_hotkey


class MenuBar(ctk.CTkFrame):
    def __init__(self, master=None, **kwargs):
        super().__init__(
            master, corner_radius=0, height=25, fg_color=curr_theme.BG_PRIMARY, **kwargs
        )

    def create_widgets(self):
        pass

    def add_menu(self, menu: "Menu") -> None:
        menu.pack(side="left")


class Menu(ctk.CTkFrame):
    menu_name: str
    sub_components: list["MenuSubComponent"]
    is_top_level: bool = True
    is_open: bool = False
    is_focused_in: bool = (
        False  # menu should close only when the mouse focus was on it and then lost
    )
    popup_menu: ctk.CTkFrame
    _command: Callable | None = None
    parent_menu: Optional["Menu"] = None
    hot_key_name: str = ""
    _hook: Optional[Callable[[], None]] = None

    def __init__(
        self,
        master=None,
        menu_name: str = "",
        hotkey: str = "",
        command: Callable | None = None,
        is_super_command: bool = False,  # use keyboard to handle this command
        **kwargs,
    ):
        if master is not None and isinstance(master, Menu):
            self.is_top_level = False
            super().__init__(
                master.popup_menu,
                corner_radius=0,
                height=25,
                fg_color=curr_theme.BG_SECONDARY,
                **kwargs,
            )
            self.parent_menu = master
            master.add_menu_item(self)
        else:
            self.is_top_level = True
            super().__init__(
                master,
                corner_radius=0,
                height=25,
                bg_color=curr_theme.BG_PRIMARY,
                **kwargs,
            )

        self.menu_name = menu_name
        self.sub_components = []

        self._command = command
        if hotkey:
            if self.is_top_level:
                raise ValueError("Hotkeys can only be registered for sub-menus")
            self.hot_key_name = translate_tkinter_bind_to_hotkey(hotkey)
            if is_super_command:
                # self._hook = keyboard.add_hotkey(
                #     self.hot_key_name.lower(),
                #     lambda: self._command() if self._command is not None else None,
                # )
                threading.Thread(target=self._hot_key_listener, daemon=True).start()
                # so what is the problem with keyboard module hotkey registration?
            else:
                # register hotkey to open this menu
                root = get_root_widget(self)
                root.bind_all(
                    hotkey,
                    lambda event: self._command()
                    if self._command is not None
                    else None,
                )

        self.create_widgets()
        # if self._hook is not None:
        #     self._reupdate_hook()   

    def _hot_key_listener(self):
        while self.winfo_exists():
            if self.hot_key_name:
                if self._command is not None:
                    keyboard.wait(self.hot_key_name.lower())
                    self._command()

    def _reupdate_hook(self):
        # we have to remove and re-add the hotkey occasionally
        # sometimes keyboard module fails to trigger the hotkey otherwise

        # oops: it seems not working at all
        if self._hook is not None:
            keyboard.remove_hotkey(self._hook)
            self._hook = keyboard.add_hotkey(
                self.hot_key_name.lower(),
                lambda: self._command() if self._command is not None else None,
            )
        UPDATE_INTERVAL_MS = 1 * 60 * 1000  # 1 minute
        self.after(UPDATE_INTERVAL_MS, self._reupdate_hook)

    def create_widgets(self):
        if self.is_top_level:
            self.create_widget_top_level()
        else:
            self.create_widget_sub_menu()
        # events after creation
        self.after(100, self._focus_checker)

    def create_widget_top_level(self):
        self.button = ctk.CTkButton(
            self,
            text=self.menu_name,
            fg_color=curr_theme.BG_PRIMARY,
            bg_color=curr_theme.BG_PRIMARY,
            text_color=curr_theme.TEXT_PRIMARY,
            hover_color=curr_theme.BG_HOVER,
            corner_radius=0,
            height=25,
            width=80,
            command=self._run_command_and_close if self._command else self.open_menu,
        )
        self.button.pack(fill="x", expand=True)

        root = get_root_widget(self)
        self.popup_menu = ctk.CTkFrame(
            master=root,
            width=20,
            corner_radius=0,
            # height=25,
        )

    def _focus_checker(self):
        mouse_x, mouse_y = get_root_widget(self).winfo_pointerxy()
        wx = self.popup_menu.winfo_rootx()
        wy = self.popup_menu.winfo_rooty()
        ww = self.popup_menu.winfo_width()
        wh = self.popup_menu.winfo_height()
        if not (wx <= mouse_x <= wx + ww and wy <= mouse_y <= wy + wh):
            new_state = False
            if self.is_focused_in:
                self.after(100, lambda: self._ask_for_close())
        else:
            new_state = True
        self.is_focused_in = new_state

        self.after(100, self._focus_checker)

    def _ask_for_close(self):
        for item in self.sub_components:
            if isinstance(item, Menu):
                item._ask_for_close()
        if not self.is_open:
            return
        if not self._query_mouse_focus_state():
            self._close()

    def _close_all(self):
        self._close()
        if self.parent_menu is not None:
            self.parent_menu._close_all()

    def _close(self):
        if not self.is_open:
            return
        self.is_open = False
        self.popup_menu.place_forget()
        for item in self.sub_components:
            if isinstance(item, Menu):
                item._close()

    def _query_mouse_focus_state(self):
        if self.is_focused_in:
            return True
        for item in self.sub_components:
            if isinstance(item, Menu):
                if item._query_mouse_focus_state():
                    return True

    def open_menu(self):
        if self.is_open:
            return
        self.is_open = True
        self.is_focused_in = False  # reset mouse focus flag when opening
        # popup menu below the button
        # get the button's position relative to the root window
        button_x = self.winfo_rootx() - get_root_widget(self).winfo_rootx()
        button_y = (
            self.winfo_rooty()
            - get_root_widget(self).winfo_rooty()
            + self.winfo_height()
        )
        # resize by scaling factor
        scal = self._get_widget_scaling()
        button_x = int(button_x / scal)
        button_y = int(button_y / scal)
        self.popup_menu.place(x=button_x, y=button_y)

    def open_sub_menu(self):
        if len(self.sub_components) == 0:
            return
        if self.is_open:
            return
        self.is_open = True
        self.is_focused_in = False  # reset mouse focus flag when opening
        # popup menu to the right of the button
        # get the button's position relative to the root window
        button_x = (
            self.winfo_rootx()
            - get_root_widget(self).winfo_rootx()
            + self.winfo_width()
        )
        button_y = self.winfo_rooty() - get_root_widget(self).winfo_rooty()
        # resize by scaling factor
        scal = self._get_widget_scaling()
        button_x = int(button_x / scal)
        button_y = int(button_y / scal)
        self.popup_menu.place(x=button_x, y=button_y)

    def create_widget_sub_menu(self):
        sub_frame = ctk.CTkFrame(
            self,
            fg_color=curr_theme.BG_PRIMARY,
            bg_color=curr_theme.BG_PRIMARY,
            corner_radius=0,
            width=100,
        )
        self.button = ctk.CTkButton(
            sub_frame,
            text=self.menu_name,
            fg_color=curr_theme.BG_PRIMARY,
            bg_color=curr_theme.BG_PRIMARY,
            text_color=curr_theme.TEXT_PRIMARY,
            hover_color=curr_theme.BG_HOVER,
            corner_radius=0,
            height=25,
            width=80,
            anchor="w",
            command=self._run_command_and_close
            if self._command
            else self.open_sub_menu,
        )

        if self.hot_key_name:
            label = ctk.CTkLabel(
                sub_frame,
                text=self.hot_key_name,
                fg_color=curr_theme.BG_PRIMARY,
                bg_color=curr_theme.BG_PRIMARY,
                text_color=curr_theme.TEXT_SECONDARY,
            )
            self.button.pack(side="left", fill="x", padx=(10, 0), expand=True)
            label.pack(side="right", padx=(0, 10))
        else:
            self.button.pack(side="left", fill="x", padx=10, expand=True)
        sub_frame.pack(fill="x", expand=True)

        self.popup_menu = ctk.CTkFrame(
            master=get_root_widget(self),
            width=20,
            corner_radius=0,
            # height=25,
        )
        if self._command is None:
            self.button.bind("<Enter>", lambda event: self.open_sub_menu())

    def add_menu_item(self, item: "MenuSubComponent") -> None:
        if self._command is not None:
            raise ValueError("Cannot add menu items to a command menu")
        self.sub_components.append(item)
        item.pack(fill="x", pady=0)

    def register_command(self, command: Callable) -> None:
        if self.sub_components:
            raise ValueError("Cannot register command to a menu with sub-components")
        self._command = command

    def add_separator(self) -> None:
        separator = Separator(master=self.popup_menu)
        self.add_menu_item(separator)

    def _run_command_and_close(self) -> None:
        if self._command is not None:
            self._command()
        self._close_all()

    def rename(self, new_name: str) -> None:
        self.menu_name = new_name
        self.button.configure(text=new_name)


class Separator(ctk.CTkFrame):
    def __init__(self, master=None, **kwargs):
        super().__init__(
            master,
            corner_radius=0,
            height=2,
            bg_color=curr_theme.BORDER_COLOR,
            **kwargs,
        )


MenuSubComponent = Menu | Separator
