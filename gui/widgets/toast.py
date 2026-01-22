import customtkinter as ctk

from typing import Literal

from gui.utils import get_root_widget

ACCEPTED_POSITIONS = Literal["center", "bottom-right"]


class Toast(ctk.CTkFrame):
    position: ACCEPTED_POSITIONS

    def __init__(
        self,
        master=None,
        message: str = "",
        duration: int = 3000,
        position: ACCEPTED_POSITIONS = "bottom-right",
        **kwargs,
    ):
        super().__init__(master, **kwargs)
        self.message = message
        self.duration = duration
        self.label = ctk.CTkLabel(self, text=message)
        self.position = position

    def show(self) -> None:
        self.label.pack(padx=10, pady=5)
        self.after(self.duration, self.destroy)
        self.place_toast()

    def place_toast(self) -> None:
        root = get_root_widget(self)
        scaling_factor = root._get_window_scaling()
        root_width = int(root.winfo_width() / scaling_factor)
        root_height = int(root.winfo_height() / scaling_factor)
        self.update_idletasks()
        toast_width = int(self.winfo_reqwidth() / scaling_factor)
        toast_height = int(self.winfo_reqheight() / scaling_factor)
        if self.position == "center":
            x = (root_width - toast_width) // 2
            y = (root_height - toast_height) // 2
        elif self.position == "bottom-right":
            x = root_width - toast_width - 20
            y = root_height - toast_height - 20
        else:
            x = 0
            y = 0
        self.place(x=x, y=y)


def raise_toast(
    master,
    message: str,
    duration: int = 3000,
    position: ACCEPTED_POSITIONS = "bottom-right",
) -> None:
    toast = Toast(
        master=get_root_widget(master),
        message=message,
        duration=duration,
        position=position,
    )
    toast.show()
