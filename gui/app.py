import customtkinter as ctk

from typing import TypedDict

from gui.mainframe import MainFrame
from shared.utils import ask_for_admin_privileges, IS_ADMIN, install_main_thread_dispatcher


class AppProps(TypedDict):
    admin: bool


def run_app(props: AppProps):
    ctk.set_appearance_mode("System")
    ctk.set_default_color_theme("blue")

    app = ctk.CTk()
    app.title("Genshin Chart Player")
    app.geometry("1200x800")
    install_main_thread_dispatcher(app)

    main_frame = MainFrame(master=app)
    main_frame.pack(fill="both", expand=True)

    if props["admin"] and (not IS_ADMIN):
        ask_for_admin_privileges()

    app.mainloop()
