import sys

import customtkinter as ctk

from gui.widgets.editor import EditorFrame
from gui.widgets.sidebar import SidebarFrame
from gui.widgets.sidebars.play import PlayFunctionalFrame
from gui.widgets.sidebars.file import FileFunctionalFrame
from gui.widgets.menubar import MenuBar, Menu
from gui.widgets.toast import raise_toast
from gui.widgets.notification import raise_bottom_warning
from gui.theme import curr_theme
from gui.utils import ask_open_file_dialog, ask_save_file_dialog, show_file_in_explorer
from shared.settings import ACCEPTED_FILE_EXTENSIONS
from shared.utils import should_request_admin_privileges, ask_for_admin_privileges
from player.handlers import imported_handler_modules
from session.manager import JSONSessionManager


class MainFrame(ctk.CTkFrame):
    master: ctk.CTk
    topmost: bool = False
    jm: JSONSessionManager

    def __init__(self, master=None, **kwargs):
        super().__init__(master, **kwargs)
        self.configure(fg_color=curr_theme.BG_SECONDARY)
        self.load_configurations()
        self.create_menu_bar()
        self.create_widgets()
        self.load_widget_configurations()
        self.default_settings()

    def load_configurations(self) -> None:
        pass

    def load_widget_configurations(self) -> None:
        self.jm = JSONSessionManager()
        self.jm.register_widget("editor", self.editor_frame)
        self.jm.register_widget("sidebar", self.sidebar_frame)
        self.jm.register_configuration("color_theme", curr_theme)
        self.jm.load_configurations()
        self.update_all_colors()

    def create_menu_bar(self):
        self.menubar = MenuBar(master=self)
        self.menubar.pack(side="top", fill="x", expand=True)

        self.file_menu = Menu(master=self.menubar, menu_name="File")
        self.menubar.add_menu(self.file_menu)

        self.new_file_menu_item = Menu(
            master=self.file_menu,
            menu_name="New File",
            command=self.handle_new_file,
            hotkey="<Control-n>",
        )

        self.open_menu_item = Menu(
            master=self.file_menu,
            menu_name="Open",
            command=self.open_file_dialog,
            hotkey="<Control-o>",
        )

        self.open_new_folder_menu_item = Menu(
            master=self.file_menu,
            menu_name="Open Folder",
            command=self.handle_new_folder,
            hotkey="<Control-Shift-O>",
        )

        self.file_menu.add_separator()
        self.save_menu_item = Menu(
            master=self.file_menu,
            menu_name="Save",
            command=self.save_current_file,
            hotkey="<Control-s>",
        )
        self.save_as_menu_item = Menu(
            master=self.file_menu,
            menu_name="Save As",
            command=self.save_current_file_as,
            hotkey="<Control-Shift-S>",
        )
        self.file_menu.add_separator()

        self.export_musicxml_menu_item = Menu(
            master=self.file_menu,
            menu_name="Export MusicXML",
            command=self.handle_editor_export_musicxml,
        )

        self.export_midi_menu_item = Menu(
            master=self.file_menu,
            menu_name="Export MIDI",
            command=self.handle_editor_export_midi,
        )

        self.export_numeral_menu_item = Menu(
            master=self.file_menu,
            menu_name="Export Numeral Notation",
            command=self.handle_export_numeral_notation,
        )

        self.file_menu.add_separator()

        self.convert_from_score_item = Menu(
            master=self.file_menu,
            menu_name="Convert from MusicXML/MIDI",
            command=self.handle_convert_from_musicxml,
        )

        self.file_menu.add_separator()

        self.quit_menu_item = Menu(
            master=self.file_menu,
            menu_name="Quit",
            command=self.quit_application,
            hotkey="<Control-q>",
        )

        self.edit_menu = Menu(master=self.menubar, menu_name="Edit")

        self.menubar.add_menu(self.edit_menu)

        self.format_menu_item = Menu(
            master=self.edit_menu,
            menu_name="Format Chart",
            command=self.handle_format_chart,
            hotkey="<Alt-Shift-F>",
        )

        self.fake_space_menu_item = Menu(
            master=self.edit_menu,
            menu_name="Replace fake spaces",
            command=self.handle_replace_fake_space,
            hotkey="<Alt-Shift-H>",
        )

        # self.undo_menu_item = Menu(
        #     master=self.edit_menu,
        #     menu_name="Undo",
        #     command=do_nothing,
        #     hotkey="<Control-z>",
        # )
        # self.redo_menu_item = Menu(
        #     master=self.edit_menu,
        #     menu_name="Redo",
        #     command=do_nothing,
        #     hotkey="<Control-y>",
        # )
        self.settings_menu = Menu(master=self.menubar, menu_name="Settings")
        self.menubar.add_menu(self.settings_menu)
        self.toggle_topmost_menu_item = Menu(
            master=self.settings_menu,
            menu_name="Enable Always on Top",
            command=self.toggle_topmost,
        )
        self.settings_menu.add_separator()
        self.handler_selection_menu_item = Menu(
            master=self.settings_menu,
            menu_name="Player Handler",
        )
        self.handler_items = {}
        for handler_name, module in imported_handler_modules.items():
            handler_menu_item = Menu(
                master=self.handler_selection_menu_item,
                menu_name=module.name(),
                command=lambda name=handler_name: self.set_handler(name),
            )
            self.handler_items[handler_name] = handler_menu_item

        self.settings_menu.add_separator()

        self.apperence_mode_menu = Menu(
            master=self.settings_menu,
            menu_name="Appearance Mode",
        )

        app_mods = [
            ("Light Mode", "light"),
            ("Dark Mode", "dark"),
            ("System Mode", "system"),
        ]
        self.mode_menu_items = {}
        for mod_name, mod_key in app_mods:
            mod_menu_item = Menu(
                master=self.apperence_mode_menu,
                menu_name=mod_name,
                command=lambda mode=mod_key: self.toggle_appearance_mode(mode),
            )
            self.mode_menu_items[mod_key] = mod_menu_item

        self.player_menu = Menu(master=self.menubar, menu_name="Play")
        self.menubar.add_menu(self.player_menu)
        self.play_menu_item = Menu(
            master=self.player_menu,
            menu_name="Play",
            command=self.player_handle_play,
            hotkey="<F5>",
            is_super_command=True,
        )
        self.play_from_start_menu_item = Menu(
            master=self.player_menu,
            menu_name="Play from Start",
            command=self.player_handle_play_from_start,
            hotkey="<Shift-F5>",
            is_super_command=True,
        )
        self.stop_menu_item = Menu(
            master=self.player_menu,
            menu_name="Stop",
            command=self.player_handle_stop,
            hotkey="<F6>",
            is_super_command=True,
        )
        self.reset_menu_item = Menu(
            master=self.player_menu,
            menu_name="Stop and Reset",
            command=self.player_handle_stop_and_reset,
            hotkey="<F7>",
            is_super_command=True,
        )

        self.player_menu.add_separator()

        self.practice_menu_item = Menu(
            master=self.player_menu,
            menu_name="Practice Mode",
            command=self.player_handle_practice,
            hotkey="<F8>",
            is_super_command=True,
        )
        self.practice_mode_reset_menu_item = Menu(
            master=self.player_menu,
            menu_name="Practice Mode (Reset)",
            command=lambda: self.player_handle_practice(reset=True),
            hotkey="<Shift-F8>",
            is_super_command=True,
        )

        self.player_menu.add_separator()

        self.enable_floating_display_menu_item = Menu(
            master=self.player_menu,
            menu_name="Toggle Floating Display",
            command=self.toggle_floating_display,
            hotkey="<F12>",
            is_super_command=True,
        )

        if should_request_admin_privileges():
            self.reopen_as_admin_menu_item = Menu(
                master=self.settings_menu,
                menu_name="Reopen as Administrator",
                command=self.handle_reopen_asministrator,
            )

    def set_handler(self, handler_name: str, silent=False) -> None:
        play_frame = self.sidebar_frame.get_functional_frame("Player")
        if isinstance(play_frame, PlayFunctionalFrame):
            play_frame.set_handler(handler_name)
            if not silent:
                raise_toast(
                    master=self,
                    message="Player handler changed successfully.",
                    duration=2000,
                    position="center",
                )

    def toggle_topmost(self) -> None:
        self.topmost = not self.topmost
        if self.topmost:
            self.toggle_topmost_menu_item.rename("Disable Always on Top")
        else:
            self.toggle_topmost_menu_item.rename("Enable Always on Top")
        self.master.wm_attributes("-topmost", self.topmost)

    def open_file_dialog(self) -> None:
        file_path = ask_open_file_dialog(ACCEPTED_FILE_EXTENSIONS)
        if file_path is not None:
            self.editor_frame.handle_open_file(file_path)

    def create_widgets(self):
        self.sidebar_frame = SidebarFrame(
            master=self, border_width=2, border_color=curr_theme.BORDER_COLOR
        )
        self.sidebar_frame.pack(side="left", fill="y", padx=10, pady=10)

        self.editor_frame = EditorFrame(master=self)
        self.editor_frame.pack(
            side="right",
            fill="both",
            expand=True,
            padx=10,
            pady=10,
        )

        self.sidebar_frame.register_open_callback(self.editor_frame.handle_open_file)
        play_frame = self.sidebar_frame.get_functional_frame("Player")
        if isinstance(play_frame, PlayFunctionalFrame):
            play_frame.bind_editor(self.editor_frame)
            self.editor_frame.register_callback(lambda _: play_frame.on_tab_switched())

    def save_current_file(self) -> None:
        curr_tab = self.editor_frame.text_areas.get_current_file_tab()
        if curr_tab is not None:
            curr_tab.update_content(self.editor_frame.text_areas.get_text_area_str())
            if curr_tab.source_path is not None:
                curr_tab.save()
                raise_toast(
                    master=self,
                    message="File saved successfully.",
                    duration=2000,
                    position="center",
                )
            else:
                # no source path, trigger save as dialog
                self.save_current_file_as()

    def save_current_file_as(self) -> None:
        curr_tab = self.editor_frame.text_areas.get_current_file_tab()
        if curr_tab is not None:
            old_name = curr_tab.tab_identifier
            old_path = curr_tab.source_path
            file_path = ask_save_file_dialog(ACCEPTED_FILE_EXTENSIONS)
            if file_path is not None:
                curr_tab.update_content(
                    self.editor_frame.text_areas.get_text_area_str()
                )
                curr_tab.save(path=file_path)
                raise_toast(
                    master=self,
                    message="File saved successfully.",
                    duration=2000,
                    position="center",
                )
                new_name = curr_tab.tab_identifier
                new_path = curr_tab.source_path
                self.editor_frame.rename_tab(old_name, new_name)
                self.editor_frame.remove_path_from_opened(old_path)
                self.editor_frame.add_path_to_opened(new_path)

    def handle_new_file(self) -> None:
        self.editor_frame.handle_new_file()

    def handle_new_folder(self) -> None:
        file_fun = self.sidebar_frame.get_functional_frame("Files")
        if isinstance(file_fun, FileFunctionalFrame):
            file_fun.open_folder_dialog()

    def toggle_appearance_mode(self, mode: str) -> None:
        ctk.set_appearance_mode(mode)

    def default_settings(self) -> None:
        default_handler = "player.handlers.sound_h"
        if default_handler in imported_handler_modules.keys():
            self.set_handler(default_handler, silent=True)

        if should_request_admin_privileges():
            raise_bottom_warning(
                master=self,
                text="Some features may require administrator privileges. "
                "You can reopen the application as administrator from the Settings menu.",
            )

        # on destroy save session
        self.master.protocol("WM_DELETE_WINDOW", self.on_close)

    def player_handle_play(self) -> None:
        play_frame = self.sidebar_frame.get_functional_frame("Player")
        if isinstance(play_frame, PlayFunctionalFrame):
            play_frame.request_play()

    def player_handle_stop(self) -> None:
        play_frame = self.sidebar_frame.get_functional_frame("Player")
        if isinstance(play_frame, PlayFunctionalFrame):
            play_frame.request_stop()

    def player_handle_stop_and_reset(self) -> None:
        play_frame = self.sidebar_frame.get_functional_frame("Player")
        if isinstance(play_frame, PlayFunctionalFrame):
            play_frame.request_stop_and_reset()

    def player_handle_play_from_start(self) -> None:
        play_frame = self.sidebar_frame.get_functional_frame("Player")
        if isinstance(play_frame, PlayFunctionalFrame):
            play_frame.request_play_from_start()

    def handle_editor_export_musicxml(self) -> None:

        stream = self.editor_frame.get_current_chart_musicxml_stream()
        if stream is not None:
            filename = f"{self.editor_frame.get_title()}.mxl"
            filepath = ask_save_file_dialog(["*.mxl"], default_filename=filename)
            if filepath is not None:
                try:
                    stream.write("musicxml", fp=filepath)
                    raise_toast(
                        master=self,
                        message="MusicXML exported successfully.",
                        duration=2000,
                        position="center",
                    )
                    show_file_in_explorer(filepath)
                except Exception as e:
                    import traceback
                    traceback.print_exc()
                    raise_bottom_warning(
                        master=self,
                        text=f"Failed to export MusicXML: {str(e)}",
                    )
        else:
            raise_bottom_warning(
                master=self,
                text="Failed to export MusicXML: No valid chart data found.",
            )

    def handle_editor_export_midi(self) -> None:
        stream = self.editor_frame.get_current_chart_musicxml_stream()

        if stream is not None:
            filename = f"{self.editor_frame.get_title()}.mid"
            filepath = ask_save_file_dialog(["*.mid"], default_filename=filename)
            if filepath is not None:
                try:
                    stream.write("midi", fp=filepath)
                    raise_toast(
                        master=self,
                        message="MIDI exported successfully.",
                        duration=2000,
                        position="center",
                    )
                    show_file_in_explorer(filepath)

                except Exception as e:
                    raise_bottom_warning(
                        master=self,
                        text=f"Failed to export MIDI: {str(e)}",
                    )

        else:
            raise_bottom_warning(
                master=self,
                text="Failed to export MIDI: No valid chart data found.",
            )

    def handle_convert_from_musicxml(self) -> None:
        file_path = ask_open_file_dialog(["*.xml", "*.mxl", "*.musicxml", "*.mid"])
        if file_path is not None:
            resp = self.editor_frame.load_from_score(file_path)
            if not resp:
                raise_toast(
                    master=self,
                    message="Failed to convert from MusicXML/MIDI. Please make sure the file is valid and try again.",
                    duration=3000,
                    position="center",
                )

    def handle_export_numeral_notation(self) -> None:
        filename = f"{self.editor_frame.get_title()}_numeral.txt"
        filepath = ask_save_file_dialog(["*.txt"], default_filename=filename)
        if filepath is not None:
            status = self.editor_frame.export_numeral_notation(filepath)
            if not status:
                raise_toast(
                    master=self,
                    message="Failed to export numeral notation.",
                    duration=3000,
                    position="center",
                )
            else:
                raise_toast(
                    master=self,
                    message="Numeral notation exported successfully.",
                    duration=2000,
                    position="center",
                )
                show_file_in_explorer(filepath)
    def handle_reopen_asministrator(self) -> None:
        if should_request_admin_privileges():
            ask_for_admin_privileges()
            sys.exit(0)

    def toggle_floating_display(self) -> None:
        play_frame = self.sidebar_frame.get_functional_frame("Player")
        if isinstance(play_frame, PlayFunctionalFrame):
            play_frame.toggle_floating_display()

    def player_handle_practice(self, reset=False) -> None:
        play_frame = self.sidebar_frame.get_functional_frame("Player")
        if isinstance(play_frame, PlayFunctionalFrame):
            play_frame.toggle_practice_mode(reset=reset)

    def quit_application(self) -> None:
        self.master.quit()

    def handle_format_chart(self) -> None:
        self.editor_frame.format_chart()

    def handle_replace_fake_space(self) -> None:
        self.editor_frame.remove_fake_spaces()

    def on_close(self) -> None:
        self.jm.save_configurations()
        self.master.destroy()

    def update_all_colors(self) -> None:
        ctk.AppearanceModeTracker.update_callbacks()
