import customtkinter as ctk
from gui.mainframe import MainFrame


def run_app():
    ctk.set_appearance_mode("System")
    ctk.set_default_color_theme("blue")

    app = ctk.CTk()
    app.title("Genshin Chart Player")
    app.geometry("1200x800")

    main_frame = MainFrame(master=app)
    main_frame.pack(fill="both", expand=True)

    app.mainloop()