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
        pass

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


class CommandRegistry:
    _commands: dict[str, type[Command]] = {}

    @classmethod
    def register_command(cls, name: str, command_cls: type[Command]) -> None:
        cls._commands[name] = command_cls

    @classmethod
    def get_command_class(cls, name: str) -> type[Command] | None:
        return cls._commands.get(name, None)
    
    def execute_command(self, name: str, args: list[str], internal_property: InternalProperty) -> None:
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
        if self.args[0] == "ts":
            return self.args[1] in ("3", "4")
        return False

    def execute(self) -> None:
        if self.args[0] == "bpm":
            self.internal_property.bpm = float(self.args[1])
        elif self.args[0] == "ts":
            self.internal_property.time_signature = int(self.args[1])  # type: ignore


default_command_registry = CommandRegistry()
default_command_registry.register_command(CMD_Set._registered_name, CMD_Set)

command_registry = default_command_registry # exported registry instance
