"""Reservation table: what the already planned drones occupy."""

from flyin.connection import Connection
from flyin.network import Network
from flyin.zone import Zone


class ReservationTable:
    """Remembers which zones and connections are taken at each turn."""

    def __init__(self, network: Network) -> None:
        """Create an empty table.

        Args:
            network: The network the drones fly in.
        """
        self.network = network
        self._zone_load: dict[tuple[str, int], int] = {}
        self._link_load: dict[tuple[frozenset[str], int], int] = {}

    def zone_has_room(self, zone: Zone, turn: int) -> bool:
        """Tell if one more drone fits in a zone at the end of a turn.

        Args:
            zone: The zone to check.
            turn: The turn number.

        Returns:
            True if the zone has room. Start and end have no limit.
        """
        if zone.is_start or zone.is_end:
            return True
        return self._zone_load.get((zone.name, turn), 0) < zone.max_drones

    def link_has_room(self, conn: Connection, turn: int) -> bool:
        """Tell if one more drone can use a connection during a turn.

        Args:
            conn: The connection to check.
            turn: The turn number.

        Returns:
            True if the connection has room.
        """
        used = self._link_load.get((conn.key, turn), 0)
        return used < conn.max_link_capacity

    def zone_usage(self, zone: Zone, turn: int) -> int:
        return self._zone_load.get((zone.name, turn), 0)

    def link_usage(self, conn: Connection, turn: int) -> int:
        return self._link_load.get((conn.key, turn), 0)

    def reserve(self, states: list[str]) -> None:
        """Reserve everything a drone uses along its path.

        Args:
            states: The state of the drone at each turn, starting at
                the start zone.
        """
        zones = self.network.zones
        for turn in range(1, len(states)):
            before, now = states[turn - 1], states[turn]
            if now in zones:
                key = (now, turn)
                self._zone_load[key] = self._zone_load.get(key, 0) + 1
            if before not in zones or now == before:
                continue
            link = frozenset((before, now) if now in zones
                             else now.split("-"))
            link_key = (link, turn)
            self._link_load[link_key] = self._link_load.get(link_key, 0) + 1
