from dataclasses import dataclass
from enum import IntEnum, StrEnum


class Kind(StrEnum):
    MESSAGE = "message"
    PROGRESS = "progress"
    MEDIA = "media"
    LEVEL = "level"


class Priority(IntEnum):
    LOW = 0
    NORMAL = 1
    HIGH = 2


@dataclass(frozen=True)
class Notification:
    id: int
    app: str
    title: str
    body: str = ""
    priority: Priority = Priority.NORMAL
    timeout: float = 5.0
    kind: Kind = Kind.MESSAGE
    value: float = 0.0
    value_label: str = ""
    status: str = ""
    artwork: str = ""
    desktop_entry: str = ""
    actions: tuple[tuple[str, str], ...] = ()

    def __post_init__(self):
        import math
        if not math.isfinite(self.value) or not 0 <= self.value <= 1:
            raise ValueError("notification value must be finite and between 0 and 1")
