from typing import Any, Protocol

from shared.rtjson import RTJSON
from shared.settings import SESSION_FILE_PATH


class SessionStore(Protocol):
    def load(self) -> dict[str, Any]: ...

    def save(self, data: dict[str, Any]) -> None: ...


class JSONSessionStore:
    session_file_path: str
    rt_json: RTJSON[dict[str, Any]]

    def __init__(self, session_file_path: str = SESSION_FILE_PATH) -> None:
        self.session_file_path = session_file_path
        self.rt_json = RTJSON[dict[str, Any]](self.session_file_path, default_data={})

    def load(self) -> dict[str, Any]:
        return self.rt_json.load()

    def save(self, data: dict[str, Any]) -> None:
        self.rt_json.save(data)