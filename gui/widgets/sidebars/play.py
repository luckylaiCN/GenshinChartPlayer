import time
import threading

import customtkinter as ctk

from gui.theme import curr_theme
from gui.widgets.sidebars.base import FunctionalFrame
from gui.widgets.editor import EditorFrame
from gui.widgets.toast import raise_toast
from gui.widgets.floating import FloatingChartDisplay
from shared.utils import global_operation_lock, OperationLockState, FlagBoolean
from player.runtime import PlayerThreadingPool
from player.handlers import imported_handler_modules, fallback_module
from player.practice import PracticeController

PLAY_CHARACTER = "▶"
PAUSE_CHARACTER = "⏯"
PLAY_STARTOVER_CHARACTER = "⟲"
STOP_CHARACTER = "■"


class PlayFunctionalFrame(FunctionalFrame):
    binded_editor: EditorFrame | None = None
    is_playing: bool = False
    is_practicing: bool = False
    handler_name: str = ""
    ptp: PlayerThreadingPool | None = None
    pc: PracticeController | None = None
    begin_time: float = 0.0
    floating_display: FloatingChartDisplay | None = None
    floating_display_visible: FlagBoolean = FlagBoolean(False)
    chart_speed: float = 1.0

    def bind_editor(self, editor: EditorFrame) -> None:
        self.binded_editor = editor

    def set_handler(self, handler_name: str) -> None:
        self.handler_name = handler_name
        self.handler_label.configure(text=f"Handler: {self.handler_string}")

    @property
    def handler_string(self) -> str:
        handler = imported_handler_modules.get(
            self.handler_name, fallback_module
        )
        if handler is None:
            return "No Handler"
        return handler.name()

    def create_widgets(self):
        # button group
        self.button_group = ctk.CTkFrame(self, fg_color=curr_theme.BG_SECONDARY)
        # text label
        self.label = ctk.CTkLabel(
            self.button_group,
            text="Playing Controls",
            text_color=curr_theme.TEXT_PRIMARY,
        )
        # handler label
        self.handler_label = ctk.CTkLabel(
            self.button_group,
            text=f"Handler: {self.handler_string}",
            text_color=curr_theme.TEXT_SECONDARY,
        )
        # play - pause button
        self.play_pause_button = ctk.CTkButton(
            self.button_group,
            text=PLAY_CHARACTER,
            fg_color=curr_theme.BTN_PRIMARY,
            command=self.handle_play_pause,
            width=50,
            font=("Consolas", 14),
        )
        # playover - stop button
        self.playover_stop_button = ctk.CTkButton(
            self.button_group,
            text=PLAY_STARTOVER_CHARACTER,
            fg_color=curr_theme.BTN_PRIMARY,
            command=self.handle_playover_stop,
            width=50,
            font=("Consolas", 14),
        )
        # pack buttons in the center

        self.label.pack(pady=10)
        self.handler_label.pack(pady=5)
        self.play_pause_button.pack(side="left", padx=10, pady=10)
        self.playover_stop_button.pack(side="right", padx=10, pady=10)
        self.button_group.pack(pady=20)

        # pratice mode button
        self.pratice_mode_button = ctk.CTkButton(
            self,
            text="Practice Mode",
            fg_color=curr_theme.BG_PRIMARY,
            text_color=curr_theme.TEXT_PRIMARY,
            command=self.toggle_practice_mode,
        )

        self.pratice_mode_button.pack(pady=10)

        # speed slider
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

        self.bind("<Destroy>", lambda e: self._on_destroy())

        self.speed_label.pack(pady=5)
        self.speed_slider.pack(pady=5)

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

    def _player_start(self, reset=False) -> bool:
        if not self._check_before_playing():
            return False
        if self.binded_editor is None or self.binded_editor.runtime is None:
            return False

        runtime = self.binded_editor.runtime
        handler_module = imported_handler_modules.get(self.handler_name, None)
        if handler_module is None:
            raise_toast(
                master=self,
                message="Select a valid handler in the settings menubar before playing.",
                duration=3000,
                position="center",
            )
            return False

        self.is_playing = True
        # disable speed change during playing, as it may cause unexpected issues. can be changed in the future if needed.
        self.speed_slider.configure(state="disabled")
        ip = runtime.internal_property
        ip.set_speed_multiplier(self.chart_speed)
        runtime.caculate_playlist()
        self.play_pause_button.configure(text=PAUSE_CHARACTER)
        global_operation_lock.set_state(OperationLockState.PLAYING)
        self.ptp = PlayerThreadingPool(
            beats=runtime.get_playlist(),
            handler=handler_module.handler,
        )
        beat = 0 if reset else self.binded_editor._curr_beat_index
        if beat < 0 or beat >= len(self.ptp.beats):
            beat = 0

        if self.floating_display is not None and self.floating_display.alive.get():
            self.floating_display.set_runtime(runtime)
            self.floating_display.set_beat_index(beat)

        self.ptp.set_beat_index(beat)
        self.binded_editor.set_current_beat_index(beat)

        threading.Thread(target=self.ptp.play_loop).start()

        self.begin_time = self.ptp.play()
        self.binded_editor.modify_editable(False)

        self.after(100, self._update_editor_current_beat)

        return True

    def _update_editor_current_beat(self):
        if self.binded_editor is None or self.ptp is None:
            return
        if self.ptp.stop_flag.get():
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
            self.after(
                1000, self._player_stop
            )  # wait a bit before stopping. otherwise last note may be cut off.

    def _update_widgets_index(self, index: int) -> None:
        if self.binded_editor is not None:
            self.binded_editor.set_current_beat_index(index)
        if self.floating_display is not None and self.floating_display.alive.get():
            self.floating_display.set_beat_index(index)

    def _player_stop(self, reset=False):
        if self.ptp is not None:
            self.ptp.stop()
        if reset and self.binded_editor is not None:
            self.binded_editor.set_current_beat_index(0)
        if self.binded_editor is not None:
            self.binded_editor.modify_editable(True)
        if self.floating_display is not None and self.floating_display.alive.get():
            self.floating_display.remove_tags()
        self.is_playing = False
        self.play_pause_button.configure(text=PLAY_CHARACTER)
        global_operation_lock.release()
        self.speed_slider.configure(state="normal")

    def handle_play_pause(self):
        if not self._check_before_playing():
            return
        if self.is_playing:
            self._player_stop()

        else:
            if global_operation_lock.is_free():
                self._player_start()

            else:
                # cannot play, already locked
                raise_toast(
                    master=self,
                    message="Cannot start playing: another operation is in progress.",
                    duration=3000,
                    position="center",
                )
                return

    def handle_playover_stop(self):
        if not self._check_before_playing():
            return
        if self.is_playing:
            self._player_stop(reset=True)
        else:
            if global_operation_lock.is_free():
                self._player_start(reset=True)
            else:
                raise_toast(
                    master=self,
                    message="Cannot start playing: another operation is in progress.",
                    duration=3000,
                    position="center",
                )
                return

    def request_play(self) -> bool:
        if not self._check_before_playing():
            return False
        if global_operation_lock.is_free():
            self._player_start()
            return True
        else:
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
        else:
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
        if global_operation_lock.is_free():
            return self._player_start(reset=True)
        else:
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
        else:
            raise_toast(
                master=self,
                message="Playing is not currently active.",
                duration=2000,
                position="center",
            )
            return False

    def enable_floating_display(self) -> None:
        if self.floating_display is None or not self.floating_display.alive.get():
            self.floating_display = FloatingChartDisplay(
                master=self,
                runtime=self.binded_editor.runtime if self.binded_editor else None,
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
            if global_operation_lock.is_free():
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
                return

    def _practice_start(self, reset=False) -> bool:
        if not self._check_before_playing():
            return False
        if self.binded_editor is None or self.binded_editor.runtime is None:
            return False

        runtime = self.binded_editor.runtime
        if self.floating_display is not None and self.floating_display.alive.get():
            self.floating_display.set_runtime(runtime)

        self.is_practicing = True
        global_operation_lock.set_state(OperationLockState.PRACTICING)
        self.pc = PracticeController(
            beat_containers=runtime.get_playlist(),
            on_update_index=self._update_widgets_index,
            on_stop=self._on_practice_stop,
        )
        beat = self.binded_editor._curr_beat_index
        if beat < 0 or beat >= len(self.pc.beat_containers):
            beat = 0
        if reset:
            beat = 0
        threading.Thread(target=self.pc.start, args=(beat,)).start()
        self._update_widgets_index(beat)
        self.binded_editor.modify_editable(False)

        return True

    def _practice_stop(self, reset=False):
        if self.pc is not None:
            self.pc.stop()
        if reset and self.binded_editor is not None:
            self.binded_editor.set_current_beat_index(0)
        if self.binded_editor is not None:
            self.binded_editor.modify_editable(True)
        if self.floating_display is not None and self.floating_display.alive.get():
            self.floating_display.remove_tags()
        self.is_practicing = False
        global_operation_lock.release()

    def _on_practice_stop(self) -> None:
        if self.binded_editor is not None:
            self.binded_editor.modify_editable(True)
        self.is_practicing = False
        self.pratice_mode_button.configure(text="Practice Mode")
        global_operation_lock.release()

    def _on_destroy(self) -> None:
        self.disable_floating_display()
        if self.is_playing:
            self._player_stop()
        if self.is_practicing:
            self._practice_stop()

    def on_tab_switched(self) -> None:
        if self.floating_display is not None and self.floating_display.alive.get():
            runtime = self.binded_editor.runtime if self.binded_editor else None
            if runtime is not None:
                self.floating_display.set_runtime(runtime)
                if len(runtime.playlist) > 0:
                    beat = (
                        self.binded_editor._curr_beat_index
                        if self.binded_editor
                        else -1
                    )
                    # beat = max(0, min(beat, len(runtime.playlist) - 1) )
                    self.floating_display.set_beat_index(beat)
                # self.floating_display.update_instantly()

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
