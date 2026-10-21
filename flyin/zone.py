"""Zone types and zone data used by the drone routing network."""

from enum import Enum
from dataclasses import dataclass


class ZoneType(Enum):
    """Classify zones by availability, travel time, and preference."""

    NORMAL = "normal"
    BLOCKED = "blocked"
    RESTRICTED = "restricted"
    PRIORITY = "priority"

    @property
    def is_passable(self) -> bool:
        """Return whether drones are allowed to enter this zone type."""
        return self is not ZoneType.BLOCKED

    @property
    def cost(self) -> int:
        """Return entry travel time in turns.

        Raises:
            ValueError: If the zone type is blocked.
        """
        if self is ZoneType.BLOCKED:
            raise ValueError("A blocked zone cannot be entered")
        return 2 if self is ZoneType.RESTRICTED else 1


@dataclass
class Zone:
    """Represent a named map zone and its occupancy restrictions.

    Start and end zones have unlimited capacity regardless of max_drones.
    """

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
        """Return whether this zone ignores the normal drone capacity."""
        return self.is_start or self.is_end
