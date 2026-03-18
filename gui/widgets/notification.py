import customtkinter as ctk

from gui.theme import curr_theme
from gui.utils import get_root_widget


class BottomWarningFrame(ctk.CTkFrame):
    def __init__(self, master=None, text="", **kwargs):
        super().__init__(
            master,
            corner_radius=0,
            height=25,
            fg_color=curr_theme.WARNING_TAG_BG,
            **kwargs,
        )
        self.label = ctk.CTkLabel(
            self,
            text=text,
            text_color=curr_theme.TEXT_PRIMARY,
        )
        self.close_button = ctk.CTkButton(
            self,
            text="✕",
            width=20,
            height=20,
            fg_color=curr_theme.WARNING_TAG_BG,
            text_color=curr_theme.TEXT_PRIMARY,
            hover_color=curr_theme.WARNING_TAG_BG,
            command=self.destroy,
        )
        font = self.label._font
        bolded = ctk.CTkFont(
            family=font._family,  # type: ignore
            size=font._size,  # type: ignore
            weight="bold",
        )
        self.label.configure(font=bolded)
        self.label.pack(side="left", padx=10)
        self.close_button.pack(side="right", padx=10)


def raise_bottom_warning(master, text: str) -> None:
    print(f"Warning: {text}")
    warning_frame = BottomWarningFrame(master=get_root_widget(master), text=text)
    warning_frame.pack(side="bottom", fill="x")
