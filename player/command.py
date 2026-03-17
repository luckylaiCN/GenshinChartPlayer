from player.interal import InternalProperty
from abc import ABC, abstractmethod


class Command(ABC):
    """
    An abstract base class for player commands.
    """

    internal_property: InternalProperty
    _registered_name: str = ""
    args: list[str] = []

    def __init__(self, internal_property: InternalProperty) -> None:
        self.internal_property = internal_property

    @abstractmethod
    def check_valid(self) -> bool:
        """
        Check if the command is valid in the current context.
        Returns True if valid, False otherwise.
        """
        return False

    def pass_args(self, args: list[str]) -> None:
        """
        Pass arguments to the command.
        """
        self.args = args

    @abstractmethod
    def execute(self) -> None:  # on runtime
        """
        Execute the command.
        """
        pass


class CommandParseError(Exception):
    def __init__(self, message: str, line_number: int) -> None:
        super().__init__(message)
        self.line_number = line_number


class CommandParseErrorInfo:
    message: str
    line_number: int

    def __init__(self, message: str, line_number: int) -> None:
        self.message = message
        self.line_number = line_number


class CommandParseException(Exception):
    def __init__(self, errors: list[CommandParseErrorInfo]) -> None:
        super().__init__("Multiple command parse errors occurred.")
        self.errors = errors


class CommandRegistry:
    _commands: dict[str, type[Command]] = {}

    @classmethod
    def register_command(cls, command_cls: type[Command]) -> None:
        cls._commands[command_cls._registered_name] = command_cls

    @classmethod
    def register_commands(cls, commands_cls: list[type[Command]]) -> None:
        for cmd_cls in commands_cls:
            cls.register_command(cmd_cls)

    @classmethod
    def get_command_class(cls, name: str) -> type[Command] | None:
        return cls._commands.get(name, None)

    def execute_command(
        self, name: str, args: list[str], internal_property: InternalProperty
    ) -> None:
        command_cls = self.get_command_class(name)
        if command_cls is None:
            raise CommandParseError(f"Unknown command: {name}", -1)
        command_instance = command_cls(internal_property)
        command_instance.pass_args(args)
        if not command_instance.check_valid():
            raise CommandParseError(f"Invalid arguments for command: {name}", -1)
        command_instance.execute()


class CMD_Set(Command):
    _registered_name = "set"

    def check_valid(self) -> bool:
        if len(self.args) != 2:
            return False
        if self.args[0] == "bpm":
            try:
                bpm_value = float(self.args[1])
                return bpm_value > 0
            except ValueError:
                return False
        return False

    def execute(self) -> None:
        if self.args[0] == "bpm":
            self.internal_property.bpm = float(self.args[1])


class CMD_Author(Command):
    _registered_name = "author"

    def check_valid(self) -> bool:
        return True

    def execute(self) -> None:
        author_name = self.args[0] if len(self.args) > 0 else "Unknown Artist"
        self.internal_property.author = author_name


default_command_registry = CommandRegistry()
default_command_registry.register_commands([CMD_Set, CMD_Author])

command_registry = default_command_registry  # exported registry instance
