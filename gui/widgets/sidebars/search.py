import customtkinter as ctk

from gui.theme import curr_theme
from gui.widgets.sidebars.base import FunctionalFrame

class SearchFunctionalFrame(FunctionalFrame):
    def create_widgets(self):
        # Add file-related buttons or options here
        self.label = ctk.CTkLabel(
            self, text="Search Page.", text_color=curr_theme.TEXT_PRIMARY
        )
        self.label.pack(pady=10)