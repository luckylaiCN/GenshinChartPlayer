import customtkinter as ctk

class ContextMenu(ctk.CTkFrame):
    def __init__(self, master=None, **kwargs):
        super().__init__(master, tearoff=0, **kwargs)