import customtkinter as ctk

from typing import TypedDict

from gui.mainframe import MainFrame
from gui.widgets.notification import raise_bottom_warning
from shared.utils import (
    CURRENT_OS,
    OperatingSystem,
    ask_for_admin_privileges,
    IS_ADMIN,
    install_main_thread_dispatcher,
)
from shared.mac_input import (
    macos_keyboard_input_permission_granted,
    macos_keyboard_injection_permission_granted,
    request_macos_keyboard_permissions,
    debug_start_global_monitor,
)


class AppProps(TypedDict):
    admin: bool


def run_app(props: AppProps):
    if CURRENT_OS == OperatingSystem.MACOS and IS_ADMIN:
        raise SystemExit("Do not run this app with sudo on macOS. Launch it normally instead.")

    ctk.set_appearance_mode("System")
    ctk.set_default_color_theme("blue")

    app = ctk.CTk()
    app.title("Genshin Chart Player")
    app.geometry("1200x800")
    install_main_thread_dispatcher(app)

    main_frame = MainFrame(master=app)
    main_frame.pack(fill="both", expand=True)

    if CURRENT_OS == OperatingSystem.MACOS:
        input_ok = macos_keyboard_input_permission_granted()
        inject_ok = macos_keyboard_injection_permission_granted()
        print(f"[app] macOS permissions input={input_ok} injection={inject_ok}")
        # Optional debug: if env var GCP_MAC_INPUT_DEBUG=1 is set, start a raw global monitor
        import os

        if os.environ.get("GCP_MAC_INPUT_DEBUG"):
            dbg_handle = debug_start_global_monitor()
            if dbg_handle is not None:
                print("[app] debug global monitor started (set GCP_MAC_INPUT_DEBUG=1 to enable)")
        if not (input_ok and inject_ok):
            request_macos_keyboard_permissions()
            missing = []
            if not input_ok:
                missing.append("Input Monitoring")
            if not inject_ok:
                missing.append("Accessibility")
            raise_bottom_warning(
                main_frame,
                "macOS keyboard permissions missing: "
                + ", ".join(missing)
                + ". Open System Settings > Privacy & Security and enable them for the app or terminal.",
            )

    if props["admin"] and (not IS_ADMIN):
        ask_for_admin_privileges()

    app.mainloop()
