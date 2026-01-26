import json

from typing import Optional, TypeVar, Generic

# implementation for real-time json on storage devices

T = TypeVar("T")


class RTJSON(Generic[T]):
    target_file: str  # path to the target json file
    data_str: str  # json data in string format
    default_data: Optional[T]  # default data to use if loading fails

    def __init__(self, target_file: str, default_data: Optional[T] = None) -> None:
        self.target_file = target_file
        self.data_str = ""
        self.default_data = default_data

    def load(self) -> T:
        try:
            with open(self.target_file, "r", encoding="utf-8") as f:
                self.data_str = f.read()
            return json.loads(self.data_str)
        except Exception as e:
            if self.default_data is not None:
                return self.default_data
            raise RuntimeError(
                f"Failed to load RTJSON from {self.target_file}: {e}, yet no default data is provided."
            ) from e

    def save(self, data: T) -> None:
        try:
            self.data_str = json.dumps(data, ensure_ascii=False, indent=4)
            with open(self.target_file, "w", encoding="utf-8") as f:
                f.write(self.data_str)
        except Exception as e:
            raise RuntimeError(
                f"Failed to save RTJSON to {self.target_file}: {e}"
            ) from e
