import customtkinter as ctk

from gui.theme import curr_theme

class FunctionalFrame(ctk.CTkFrame):
    internal_width: int

    def __init__(self, master=None, **kwargs):
        super().__init__(master, **kwargs)
        self.internal_width = 200
        self.configure(width=self.internal_width, fg_color=curr_theme.BG_SECONDARY)
        self.pack_propagate(False)
        self.create_widgets()

    def create_widgets(self):
        # Placeholder for functional buttons or options
        self.label = ctk.CTkLabel(self, text="Functions")
        self.label.pack(pady=10)

    def set_width(self, width: int) -> None:
        self.internal_width = width
        self.configure(width=width, fg_color=curr_theme.BG_SECONDARY)
        self.update()