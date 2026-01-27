# save and load session when opening/closing the program

from typing import Any, TypedDict
from contextlib import suppress

from session.base import RecoverableWidget, ConfigurationItem, VERSION
from shared.utils import SYSTEM_USER_UNIQUE_ID
from shared.settings import SESSION_FILE_PATH
from shared.rtjson import RTJSON

class JSONSessionData(TypedDict):
    version: int
    configurations: dict[str, Any]
    widgets: dict[str, Any]


class JSONSessionManager:
    registered_widgets: dict[str, RecoverableWidget]
    registered_configurations: dict[str, ConfigurationItem]
    session_file_path: str
    owner: str
    new_user: bool = True
    version: int = -1
    rt_json: RTJSON[dict[str, JSONSessionData]]

    def __init__(self, session_file_path: str = SESSION_FILE_PATH) -> None:
        self.registered_configurations = {}
        self.registered_widgets = {}
        self.session_file_path = session_file_path
        self.owner = SYSTEM_USER_UNIQUE_ID
        self.new_user = True
        self.version = -1
        self.rt_json = RTJSON[dict[str, JSONSessionData]](
            self.session_file_path, default_data={}
        )

    def register_widget(self, name: str, widget: RecoverableWidget) -> None:
        self.registered_widgets[name] = widget

    def register_configuration(
        self, name: str, configuration: ConfigurationItem
    ) -> None:
        self.registered_configurations[name] = configuration

    def cleanup_outdated_sessions(self) -> None:
        all_data = self.rt_json.load()
        valid_data: dict[str, JSONSessionData] = {}
        for owner, data in all_data.items():
            if data.get("version", -1) == VERSION:
                valid_data[owner] = data
        self.rt_json.save(valid_data)

    def _dump_session_kw(self) -> dict[str, JSONSessionData]:
        widgets_data: dict[str, Any] = {}
        for name, widget in self.registered_widgets.items():
            widgets_data[name] = widget.dump_session()
        configurations: dict[str, Any] = {}
        for name, config in self.registered_configurations.items():
            configurations[name] = config.dump_configuration()
        session_data: JSONSessionData = {
            "version": VERSION,
            "configurations": configurations,
            "widgets": widgets_data,
        }
        return {SYSTEM_USER_UNIQUE_ID: session_data}

    def _load_user_session(self, data: JSONSessionData) -> None:
        if data.get("version", -1) != VERSION:
            return  # do not load incompatible session versions

        self.new_user = False
        configurations = data.get("configurations", {})
        widget_data = data.get("widgets", {})
        for name, widget in self.registered_widgets.items():
            if name in widget_data:
                with suppress(Exception):
                    widget.load_session(widget_data[name])
        for name, config in self.registered_configurations.items():
            if name in configurations:
                with suppress(Exception):
                    config.load_configuration(configurations[name])

    def load_configurations(self) -> None:
        all_data = self.rt_json.load()
        if self.owner in all_data:
            self._load_user_session(all_data[self.owner])
        self.cleanup_outdated_sessions()

    def save_configurations(self) -> None:
        all_data = self.rt_json.load()
        all_data.update(self._dump_session_kw())
        self.rt_json.save(all_data)
