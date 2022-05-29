from enum import Enum
from dataclasses import dataclass, field

class CommandType(Enum):
    StopContainer = 10
    StartContainer = 20
    UpdateDevice = 100
    ReadCompose = 110
    WriteCompose = 111

@dataclass
class Command:
    """Command object. Defines the command message to clients"""
    type: CommandType
    payload: dict = field(default_factory=dict)

