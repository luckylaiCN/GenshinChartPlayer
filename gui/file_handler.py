import random
import os


def random_string(length: int) -> str:
    """Generate a random string of fixed length."""
    letters = "0123456789abcdef"
    return "".join(random.choice(letters) for _ in range(length))


class IdentifierGenerator:
    """A simple identifier generator that produces unique string IDs."""

    existing_ids: set[str]

    def __init__(self) -> None:
        self.existing_ids = set()

    def generate_id(self, length: int = 6) -> str:
        """Generate a unique identifier of specified length."""
        while True:
            new_id = random_string(length)
            if new_id not in self.existing_ids:
                self.existing_ids.add(new_id)
                return new_id

    def release_id(self, id_to_release: str) -> None:
        """Release an identifier back to the pool."""
        self.existing_ids.discard(id_to_release)


_ig = IdentifierGenerator()


class FileTab:
    source_path: str | None
    is_modified: bool
    editing_content: str
    internal_id: str

    def __init__(self, source_path: str | None) -> None:
        self.source_path = source_path
        self.is_modified = False
        if source_path is not None:
            self._load_from_file(source_path)
        else:
            self.editing_content = ""

        self.internal_id = _ig.generate_id(6)

    def _load_from_file(self, path: str) -> None:
        with open(path, "r", encoding="utf-8") as f:
            self.editing_content = f.read()

    def _save_to_file(self, path: str) -> None:
        with open(path, "w", encoding="utf-8") as f:
            f.write(self.editing_content)

    def update_content(self, new_content: str) -> None:
        if new_content != self.editing_content:
            self.editing_content = new_content
            self.is_modified = True

    def save(self, path: str | None = None) -> None:
        self.is_modified = True # always consider modified after save call
        if path is not None:
            self._save_to_file(path)
            self.source_path = path
        elif self.source_path is not None:
            self._save_to_file(self.source_path)
        else:
            raise ValueError("No path specified for saving the file.")

    @staticmethod
    def new_tab() -> "FileTab":  # creates a new untitled tab
        return FileTab(source_path=None)

    @staticmethod
    def from_file(source_path: str) -> "FileTab":
        return FileTab(source_path=source_path)

    @property
    def display_name(self) -> str:
        if self.source_path is not None:
            basename = os.path.basename(self.source_path)
            filename_only, _ = os.path.splitext(basename)
            return filename_only
        else:
            return "Untitled"

    @property
    def tab_identifier(self) -> str:
        return self.display_name + "_" + self.internal_id
