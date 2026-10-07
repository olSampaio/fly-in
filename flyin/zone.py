from enum import Enum
from dataclasses import dataclass


class ZoneType(Enum):
    NORMAL = "normal"
    BLOCKED = "blocked"
    RESTRICTED = "restricted"
    PRIORITY = "priority"

    @property
    def is_passable(self) -> bool:
        return self is not ZoneType.BLOCKED

    @property
    def cost(self) -> int:
        if self is ZoneType.BLOCKED:
            raise ValueError("A blocked zone cannot be entered")
        return 2 if self is ZoneType.RESTRICTED else 1


@dataclass
class Zone:
    name: str
    x: int
    y: int
    zone_type: ZoneType = ZoneType.NORMAL
    color: str | None = None
    max_drones: int = 1
    is_start: bool = False
    is_end: bool = False

    @property
    def is_unlimited(self) -> bool:
        return self.is_start or self.is_end
