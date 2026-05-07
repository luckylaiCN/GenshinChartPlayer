import os
import time

import customtkinter as ctk

from gui.theme import curr_theme
from gui.widgets.sidebars.base import FunctionalFrame
from gui.widgets.editor import EditorFrame
from gui.widgets.toast import raise_toast
from gui.widgets.floating import FloatingChartDisplay
from gui.widgets.playlist_floating import PlaylistFloatingWindow
from gui.utils import ask_open_file_dialog
from shared.settings import ACCEPTED_FILE_EXTENSIONS
from shared.utils import (
    is_operation_free,
    set_operation_state,
    release_operation,
    OperationLockState,
    FlagBoolean,
)
from player.service import PlaybackService
from player.practice_service import PracticeService
from player.handlers import get_handler_module, get_fallback_handler_module
from player.playlist import Playlist
from player.runtime import build_chart_runtime
from chart.parser import parse_chart, ChartParseException
from player.command import CommandParseException
from player.pattern import PatternMismatchException

PLAY_CHAR = "▶"
PAUSE_CHAR = "⏸"
STOP_CHAR = "■"
NEXT_CHAR = "⏭"
PREV_CHAR = "⏮"
PLAY_STARTOVER_CHAR = "⟲"


class PlayFunctionalFrame(FunctionalFrame):
    binded_editor: EditorFrame | None = None
    is_playing: bool = False
    is_practicing: bool = False
    handler_name: str = ""
    playback_service: PlaybackService | None = None
    practice_service: PracticeService | None = None
    begin_time: float = 0.0
    floating_display: FloatingChartDisplay | None = None
    floating_display_visible: FlagBoolean = FlagBoolean(False)
    chart_speed: float = 1.0

    playlist: Playlist
    playlist_selected_index: int = -1
    _playlist_playing: bool = False
    _playlist_runtime = None
    _monitoring: bool = False
    _pl_window: PlaylistFloatingWindow | None = None

    def __init__(self, master=None, **kwargs):
        self.playlist = Playlist()
        super().__init__(master, **kwargs)

    def bind_editor(self, editor: EditorFrame) -> None:
        self.binded_editor = editor

    def set_handler(self, handler_name: str) -> None:
        self.handler_name = handler_name
        self.handler_label.configure(text=f"Handler: {self.handler_string}")

    @property
    def handler_string(self) -> str:
        handler = get_handler_module(self.handler_name) or get_fallback_handler_module()
        if handler is None:
            return "No Handler"
        return handler.name()

    def create_widgets(self):
        if self.playback_service is None:
            self.playback_service = PlaybackService()
        if self.practice_service is None:
            self.practice_service = PracticeService()

        self._create_playback_controls()
        self._create_playlist_section()

        self.bind("<Destroy>", lambda e: self._on_destroy())

    def _create_playback_controls(self):
        self.button_group = ctk.CTkFrame(self, fg_color=curr_theme.BG_SECONDARY)
        self.label = ctk.CTkLabel(
            self.button_group,
            text="Playing Controls",
            text_color=curr_theme.TEXT_PRIMARY,
        )
        self.handler_label = ctk.CTkLabel(
            self.button_group,
            text=f"Handler: {self.handler_string}",
            text_color=curr_theme.TEXT_SECONDARY,
        )

        self.play_pause_button = ctk.CTkButton(
            self.button_group,
            text=PLAY_CHAR,
            fg_color=curr_theme.BTN_PRIMARY,
            command=self.handle_play_pause,
            width=50,
            font=("Consolas", 14),
        )
        self.playover_stop_button = ctk.CTkButton(
            self.button_group,
            text=PLAY_STARTOVER_CHAR,
            fg_color=curr_theme.BTN_PRIMARY,
            command=self.handle_playover_stop,
            width=50,
            font=("Consolas", 14),
        )

        self.label.pack(pady=10)
        self.handler_label.pack(pady=5)
        self.play_pause_button.pack(side="left", padx=10, pady=10)
        self.playover_stop_button.pack(side="right", padx=10, pady=10)
        self.button_group.pack(pady=10, fill="x")

        self.pratice_mode_button = ctk.CTkButton(
            self,
            text="Practice Mode",
            fg_color=curr_theme.BG_PRIMARY,
            text_color=curr_theme.TEXT_PRIMARY,
            command=self.toggle_practice_mode,
        )
        self.pratice_mode_button.pack(pady=5)

        self.speed_label = ctk.CTkLabel(
            self,
            text="Speed 1.0x",
            text_color=curr_theme.TEXT_PRIMARY,
        )
        self.speed_slider = ctk.CTkSlider(
            self,
            number_of_steps=15,
            command=self.on_speed_change,
        )
        self.speed_label.pack(pady=2)
        self.speed_slider.pack(pady=2, padx=5)

    def _create_playlist_section(self):
        sep = ctk.CTkFrame(self, height=2, fg_color=curr_theme.BORDER_COLOR)
        sep.pack(fill="x", padx=10, pady=5)

        self.pl_toggle_btn = ctk.CTkButton(
            self,
            text="Show Playlist",
            fg_color=curr_theme.BTN_PRIMARY,
            command=self.toggle_playlist_window,
        )
        self.pl_toggle_btn.pack(pady=5)

    # --- playlist floating window ---

    def _pl_rebuild_list(self) -> None:
        if self._pl_window is not None and self._pl_window.winfo_exists():
            self._pl_window.request_rebuild()

    def _pl_update_controls_state(self) -> None:
        if self._pl_window is not None and self._pl_window.winfo_exists():
            self._pl_window._update_controls_state()

    def _pl_show_window(self) -> None:
        if self._pl_window is None or not self._pl_window.winfo_exists():
            self._pl_window = PlaylistFloatingWindow(play_frame=self)
        self._pl_window.deiconify()
        self._pl_window.lift()
        self._pl_window.focus()
        self.pl_toggle_btn.configure(text="Hide Playlist")

    def _pl_hide_window(self) -> None:
        if self._pl_window is not None and self._pl_window.winfo_exists():
            self._pl_window.withdraw()
        self.pl_toggle_btn.configure(text="Show Playlist")

    def toggle_playlist_window(self) -> None:
        if self._pl_window is not None and self._pl_window.winfo_exists():
            if self._pl_window.winfo_viewable():
                self._pl_hide_window()
                return
        self._pl_show_window()

    # --- playlist operations ---

    def _pl_on_add(self) -> None:
        paths = ask_open_file_dialog(ACCEPTED_FILE_EXTENSIONS, multiple=True)
        if paths is None:
            return
        if isinstance(paths, str):
            paths = [paths]
        for fp in paths:
            if os.path.isfile(fp):
                self.playlist.add_entry(fp)
        self._pl_rebuild_list()
        self._pl_update_controls_state()

    def _pl_on_add_current(self) -> None:
        if self.binded_editor is None:
            return
        tab = self.binded_editor.text_areas.get_current_file_tab()
        if tab is None or tab.source_path is None:
            raise_toast(
                self,
                "Please save the current file before adding to playlist.",
                3000, "center",
            )
            return
        fp = tab.source_path
        if not os.path.isfile(fp):
            return
        for e in self.playlist.entries:
            if os.path.normpath(e.file_path) == os.path.normpath(fp):
                raise_toast(self, "File is already in the playlist.", 2000, "center")
                return
        self.playlist.add_entry(fp)
        self._pl_rebuild_list()
        self._pl_update_controls_state()
        raise_toast(self, "Added current file to playlist.", 2000, "center")

    def _pl_on_remove(self) -> None:
        idx = self.playlist_selected_index
        if idx < 0 or idx >= len(self.playlist.entries):
            return
        if self._playlist_playing and idx == self.playlist.current_index:
            self._pl_stop_playback()
        self.playlist.remove_entry(idx)
        if self.playlist_selected_index >= len(self.playlist.entries):
            self.playlist_selected_index = len(self.playlist.entries) - 1
        self._pl_rebuild_list()
        self._pl_update_controls_state()

    def _pl_on_clear(self) -> None:
        if self._playlist_playing:
            self._pl_stop_playback()
        self.playlist.clear()
        self.playlist_selected_index = -1
        self._pl_rebuild_list()
        self._pl_update_controls_state()

    def _pl_on_move_up(self) -> None:
        idx = self.playlist_selected_index
        if idx > 0:
            self.playlist.move_up(idx)
            self.playlist_selected_index = idx - 1
            self._pl_rebuild_list()

    def _pl_on_move_down(self) -> None:
        idx = self.playlist_selected_index
        if 0 <= idx < len(self.playlist.entries) - 1:
            self.playlist.move_down(idx)
            self.playlist_selected_index = idx + 1
            self._pl_rebuild_list()

    def _pl_select_entry(self, index: int) -> None:
        self.playlist_selected_index = index
        self._pl_rebuild_list()

    def _pl_on_play_pause(self) -> None:
        if self._playlist_playing:
            self._pl_stop_playback()
        else:
            if self.playlist_selected_index >= 0:
                self.playlist.set_current(self.playlist_selected_index)
            self._pl_start_playback()

    def _pl_on_next(self) -> None:
        if self.playlist.is_empty:
            return
        was_playing = self._playlist_playing
        if was_playing:
            self._pl_stop_playback(mute=True)
        next_idx = self.playlist.get_next_index()
        if next_idx >= 0:
            self.playlist.set_current(next_idx)
            self.playlist_selected_index = next_idx
            self._pl_rebuild_list()
            if was_playing:
                self._pl_start_playback()

    def _pl_on_prev(self) -> None:
        if self.playlist.is_empty:
            return
        was_playing = self._playlist_playing
        if was_playing:
            self._pl_stop_playback(mute=True)
        prev_idx = self.playlist.get_prev_index()
        if prev_idx >= 0:
            self.playlist.set_current(prev_idx)
            self.playlist_selected_index = prev_idx
            self._pl_rebuild_list()
            if was_playing:
                self._pl_start_playback()

    def _pl_on_stop(self) -> None:
        self._pl_stop_playback()

    def _pl_update_floating_track_info(self) -> None:
        if self.floating_display is None or not self.floating_display.alive.get():
            return
        current = self.playlist.current_entry
        next_idx = self.playlist.get_next_index()
        if next_idx >= 0 and next_idx != self.playlist.current_index:
            next_entry = self.playlist.entries[next_idx]
            self.floating_display.set_playlist_track_info(
                current.title if current else "", next_entry.title
            )
        else:
            self.floating_display.set_playlist_track_info(
                current.title if current else ""
            )

    def _pl_start_playback(self) -> None:
        if self.playlist.is_empty:
            raise_toast(self, "Playlist is empty.", 2000, "center")
            return
        entry = self.playlist.current_entry
        if entry is None:
            return
        if not is_operation_free():
            raise_toast(self, "Another operation is in progress.", 3000, "center")
            return

        handler_module = get_handler_module(self.handler_name)
        if handler_module is None:
            raise_toast(
                self, "Select a valid handler in Settings menu.", 3000, "center"
            )
            return

        try:
            with open(entry.file_path, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception as e:
            raise_toast(self, f"Cannot read file: {e}", 3000, "center")
            return

        try:
            lines = parse_chart(content)
        except ChartParseException as e:
            msg = "; ".join(err.message for err in e.errors)
            raise_toast(self, f"Parse error: {msg}", 4000, "center")
            return

        try:
            runtime = build_chart_runtime(lines)
        except (PatternMismatchException, CommandParseException) as e:
            raise_toast(self, f"Runtime error: {e}", 4000, "center")
            return

        self._playlist_playing = True
        self._playlist_runtime = runtime
        set_operation_state(OperationLockState.PLAYING)
        self.speed_slider.configure(state="disabled")

        if self.playback_service is None:
            self.playback_service = PlaybackService()
        self.begin_time = self.playback_service.start(
            runtime=runtime,
            handler_module=handler_module,
            speed_multiplier=self.chart_speed,
            beat_index=0,
        )

        self._pl_show_floating(runtime)
        self._pl_update_floating_track_info()
        self._pl_rebuild_list()
        self._pl_update_controls_state()
        self._pl_start_monitoring()

    def _pl_stop_playback(self, mute: bool = False) -> None:
        if self.playback_service is not None:
            self.playback_service.stop()
        self._playlist_playing = False
        self._playlist_runtime = None
        self._monitoring = False
        self.speed_slider.configure(state="normal")
        if self.floating_display is not None and self.floating_display.alive.get():
            self.floating_display.remove_tags()
            self.floating_display.set_playlist_track_info("")
            self.floating_display.withdraw()
        self._pl_rebuild_list()
        self._pl_update_controls_state()
        release_operation()

    def _pl_start_monitoring(self) -> None:
        if self._monitoring:
            return
        self._monitoring = True
        self._pl_monitor_loop()

    def _pl_monitor_loop(self) -> None:
        if not self._monitoring or not self._playlist_playing:
            return
        if self.playback_service is None or self.playback_service.ptp is None:
            self.after(100, self._pl_monitor_loop)
            return
        if self.playback_service.ptp.stop_flag.get():
            self._pl_on_track_end()
            return
        if self._playlist_runtime is not None:
            runtime = self._playlist_runtime
            beats = runtime.get_playlist()
            index = 0
            while index < len(beats) and beats[index].begin_time + self.begin_time < time.time():
                index += 1
            current_beat = max(0, index - 1)
            if self.floating_display is not None and self.floating_display.alive.get():
                self.floating_display.set_beat_index(current_beat)
        self.after(100, self._pl_monitor_loop)

    def _pl_on_track_end(self) -> None:
        was_playing = self._playlist_playing
        self._monitoring = False
        self._pl_stop_playback(mute=True)
        if not was_playing:
            return
        next_idx = self.playlist.get_next_index()
        if next_idx < 0:
            self._pl_rebuild_list()
            return
        self.playlist.set_current(next_idx)
        self.playlist_selected_index = next_idx
        self._pl_rebuild_list()
        self._pl_start_playback()

    def _pl_show_floating(self, runtime) -> None:
        if self.floating_display is None or not self.floating_display.alive.get():
            self.floating_display = FloatingChartDisplay(
                master=self,
                runtime=runtime,
                indicator=self.floating_display_visible,
            )
            self.floating_display.geometry("600x100")
            self.floating_display.center_on_screen()
            self.floating_display_visible.modify(True)
        else:
            self.floating_display.set_runtime(runtime)
            self.floating_display.deiconify()
            self.floating_display.lift()
        self.floating_display.set_beat_index(0)

    # --- standard editor-based playback (unchanged) ---

    def on_speed_change(self, value: float) -> None:
        min_speed = 0.5
        max_speed = 2.0
        speed = min_speed + (max_speed - min_speed) * value
        self.speed_label.configure(text=f"Speed {speed:.2f}x")
        self.chart_speed = speed

    def _check_before_playing(self) -> bool:
        if self.binded_editor is None:
            return False
        if self.binded_editor.text_areas.curr_text_area is None:
            raise_toast(
                master=self,
                message="Open or create a new chart to get started.",
                duration=3000,
                position="center",
            )
            return False
        if self.binded_editor.runtime is None:
            raise_toast(
                master=self,
                message="No chart loaded in the editor. Please check error messages.",
                duration=3000,
                position="center",
            )
            return False
        return True

    def _is_playback_running(self) -> bool:
        if self.is_playing:
            return True
        if self.playback_service is None:
            return False
        return self.playback_service.is_running()

    def _player_start(self, reset=False) -> bool:
        if not self._check_before_playing():
            return False
        if self.binded_editor is None or self.binded_editor.runtime is None:
            return False
        if self._is_playback_running():
            return False

        runtime = self.binded_editor.runtime
        handler_module = get_handler_module(self.handler_name)
        if handler_module is None:
            raise_toast(
                master=self,
                message="Select a valid handler in the settings menubar before playing.",
                duration=3000,
                position="center",
            )
            return False

        self.is_playing = True
        self.speed_slider.configure(state="disabled")
        self.play_pause_button.configure(text=PAUSE_CHAR)
        set_operation_state(OperationLockState.PLAYING)
        if self.playback_service is None:
            self.playback_service = PlaybackService()
        beat = 0 if reset else self.binded_editor._curr_beat_index
        if beat < 0 or beat >= len(runtime.get_playlist()):
            beat = 0

        if self.floating_display is not None and self.floating_display.alive.get():
            self.floating_display.set_runtime(runtime)
            self.floating_display.set_beat_index(beat)

        self.begin_time = self.playback_service.start(
            runtime=runtime,
            handler_module=handler_module,
            speed_multiplier=self.chart_speed,
            beat_index=beat,
        )
        self.playback_service.set_beat_index(beat)
        self.binded_editor.set_current_beat_index(beat)
        self.binded_editor.modify_editable(False)

        self.after(100, self._update_editor_current_beat)
        return True

    def _update_editor_current_beat(self):
        if self.binded_editor is None or self.playback_service is None:
            return
        if self.playback_service.ptp is None:
            return
        if self.playback_service.ptp.stop_flag.get():
            if self.is_playing:
                self._player_stop()
            return
        editor_index = self.binded_editor._curr_beat_index
        editor_index = max(0, editor_index)
        desired_index = editor_index
        runtime = self.binded_editor.runtime
        if runtime is None:
            return
        while (
            runtime.playlist[desired_index].begin_time + self.begin_time < time.time()
        ):
            desired_index += 1
            if desired_index >= len(runtime.playlist):
                break
        self._update_widgets_index(desired_index - 1)
        if desired_index < len(runtime.playlist):
            self.after(100, self._update_editor_current_beat)
        else:
            self.after(1000, self._player_stop)

    def _update_widgets_index(self, index: int) -> None:
        if self.binded_editor is not None:
            self.binded_editor.set_current_beat_index(index)
        if self.floating_display is not None and self.floating_display.alive.get():
            self.floating_display.set_beat_index(index)

    def _player_stop(self, reset=False):
        if self.playback_service is not None:
            self.playback_service.stop()
        if reset and self.binded_editor is not None:
            self.binded_editor.set_current_beat_index(0)
        if self.binded_editor is not None:
            self.binded_editor.modify_editable(True)
        if self.floating_display is not None and self.floating_display.alive.get():
            self.floating_display.remove_tags()
        self.is_playing = False
        self.play_pause_button.configure(text=PLAY_CHAR)
        release_operation()
        self.speed_slider.configure(state="normal")

    def handle_play_pause(self):
        if not self._check_before_playing():
            return
        if self.is_playing:
            self._player_stop()
        else:
            if is_operation_free():
                self._player_start()
            else:
                raise_toast(
                    master=self,
                    message="Cannot start playing: another operation is in progress.",
                    duration=3000,
                    position="center",
                )

    def handle_playover_stop(self):
        if not self._check_before_playing():
            return
        if self.is_playing:
            self._player_stop(reset=True)
        else:
            if is_operation_free():
                self._player_start(reset=True)
            else:
                raise_toast(
                    master=self,
                    message="Cannot start playing: another operation is in progress.",
                    duration=3000,
                    position="center",
                )

    def request_play(self) -> bool:
        if not self._check_before_playing():
            return False
        if is_operation_free() and not self._is_playback_running():
            self._player_start()
            return True
        raise_toast(
            master=self,
            message="Cannot start playing: another operation is in progress.",
            duration=3000,
            position="center",
        )
        return False

    def request_stop(self) -> bool:
        if self.is_playing:
            self._player_stop()
            return True
        raise_toast(
            master=self,
            message="Playing is not currently active.",
            duration=2000,
            position="center",
        )
        return False

    def request_play_from_start(self) -> bool:
        if not self._check_before_playing():
            return False
        if is_operation_free() and not self._is_playback_running():
            return self._player_start(reset=True)
        raise_toast(
            master=self,
            message="Cannot start playing: another operation is in progress.",
            duration=3000,
            position="center",
        )
        return False

    def request_stop_and_reset(self) -> bool:
        if self.is_playing:
            self._player_stop(reset=True)
            return True
        raise_toast(
            master=self,
            message="Playing is not currently active.",
            duration=2000,
            position="center",
        )
        return False

    def enable_floating_display(self) -> None:
        if self.floating_display is None or not self.floating_display.alive.get():
            rt = self._playlist_runtime if self._playlist_playing else (
                self.binded_editor.runtime if self.binded_editor else None
            )
            self.floating_display = FloatingChartDisplay(
                master=self,
                runtime=rt,
                indicator=self.floating_display_visible,
            )
            self.floating_display.geometry("600x100")
            self.floating_display.center_on_screen()
        self.floating_display.deiconify()
        self.floating_display.lift()
        self.floating_display.auto_justify_window()

    def disable_floating_display(self) -> None:
        if self.floating_display is not None and self.floating_display.alive.get():
            self.floating_display.alive.modify(False)
            self.floating_display.destroy()
            self.floating_display = None

    def toggle_floating_display(self) -> None:
        if self.floating_display_visible.get():
            self.disable_floating_display()
            self.floating_display_visible.modify(False)
        else:
            self.enable_floating_display()
            self.floating_display_visible.modify(True)

    def toggle_practice_mode(self, reset=False) -> None:
        if self.is_practicing:
            self._practice_stop(reset=reset)
            self.pratice_mode_button.configure(text="Practice Mode")
        else:
            if is_operation_free():
                if not self._practice_start(reset=reset):
                    return
                self.pratice_mode_button.configure(text="Exit Practice Mode")
            else:
                raise_toast(
                    master=self,
                    message="Cannot start practice mode: another operation is in progress.",
                    duration=3000,
                    position="center",
                )

    def _practice_start(self, reset=False) -> bool:
        if not self._check_before_playing():
            return False
        if self.binded_editor is None or self.binded_editor.runtime is None:
            return False

        runtime = self.binded_editor.runtime
        if self.floating_display is not None and self.floating_display.alive.get():
            self.floating_display.set_runtime(runtime)

        self.is_practicing = True
        set_operation_state(OperationLockState.PRACTICING)
        beat = self.binded_editor._curr_beat_index
        if beat < 0 or beat >= len(runtime.get_playlist()):
            beat = 0
        if reset:
            beat = 0
        if self.practice_service is None:
            self.practice_service = PracticeService()
        started = self.practice_service.start(
            beat_containers=runtime.get_playlist(),
            begin_beat_index=beat,
            on_update_index=self._update_widgets_index,
            on_stop=self._on_practice_stop,
        )
        if not started:
            self.is_practicing = False
            release_operation()
            return False
        self._update_widgets_index(beat)
        self.binded_editor.modify_editable(False)
        return True

    def _practice_stop(self, reset=False):
        if self.practice_service is not None:
            self.practice_service.stop()
        if reset and self.binded_editor is not None:
            self.binded_editor.set_current_beat_index(0)
        if self.binded_editor is not None:
            self.binded_editor.modify_editable(True)
        if self.floating_display is not None and self.floating_display.alive.get():
            self.floating_display.remove_tags()
        self.is_practicing = False
        release_operation()

    def _on_practice_stop(self) -> None:
        if self.binded_editor is not None:
            self.binded_editor.modify_editable(True)
        self.is_practicing = False
        self.pratice_mode_button.configure(text="Practice Mode")
        release_operation()

    def _on_destroy(self) -> None:
        if self._pl_window is not None and self._pl_window.winfo_exists():
            self._pl_window.destroy()
            self._pl_window = None
        self.disable_floating_display()
        if self.is_playing:
            self._player_stop()
        if self.is_practicing:
            self._practice_stop()
        if self._playlist_playing:
            self._pl_stop_playback()

    def on_tab_switched(self) -> None:
        if self.floating_display is not None and self.floating_display.alive.get():
            if self._playlist_playing:
                return
            runtime = self.binded_editor.runtime if self.binded_editor else None
            if runtime is not None:
                self.floating_display.set_runtime(runtime)
                if len(runtime.playlist) > 0:
                    beat = (
                        self.binded_editor._curr_beat_index
                        if self.binded_editor
                        else -1
                    )
                    self.floating_display.set_beat_index(beat)

    # --- session persistence ---

    def dump_session(self) -> dict:
        return self.playlist.dump_configuration()

    def load_session(self, data: dict) -> None:
        self.playlist.load_configuration(data)
        if self._pl_window is not None and self._pl_window.winfo_exists():
            self._pl_window.mode_var.set(self.playlist.play_mode.value)
        self._pl_rebuild_list()
        self._pl_update_controls_state()

    def _set_appearance_mode(self, mode_string):
        super()._set_appearance_mode(mode_string)
        self.button_group.configure(fg_color=curr_theme.BG_SECONDARY)
        self.label.configure(text_color=curr_theme.TEXT_PRIMARY)
        self.handler_label.configure(text_color=curr_theme.TEXT_SECONDARY)
        self.play_pause_button.configure(fg_color=curr_theme.BTN_PRIMARY)
        self.playover_stop_button.configure(fg_color=curr_theme.BTN_PRIMARY)
        self.pratice_mode_button.configure(
            fg_color=curr_theme.BG_PRIMARY, text_color=curr_theme.TEXT_PRIMARY
        )
        self._pl_rebuild_list()
