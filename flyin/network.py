from flyin.connection import Connection
from flyin.zone import Zone


class Network:
    def __init__(self, nb_drones: int) -> None:
        self.nb_drones = nb_drones
        self.zones: dict[str, Zone] = {}
        self.connections: dict[frozenset[str], Connection] = {}
        self._adjacency: dict[str, list[Connection]] = {}
        self.start: Zone | None = None
        self.end: Zone | None = None

    def add_zone(self, zone: Zone) -> None:
        if zone.name in self.zones:
            raise ValueError(f"Duplicated zone name: {zone.name}")
        self.zones[zone.name] = zone
        self._adjacency[zone.name] = []
        if zone.is_start:
            self.start = zone
        if zone.is_end:
            self.end = zone

    def add_connection(self, conn: Connection) -> None:
        for name in (conn.zone_a, conn.zone_b):
            if name not in self.zones:
                raise ValueError(f"Unknown name: {name}")
        if conn.key in self.connections:
            raise ValueError(f"Duplicate connection {conn.name}")
        self.connections[conn.key] = conn
        self._adjacency[conn.zone_a].append(conn)
        self._adjacency[conn.zone_b].append(conn)

    def neighbours(self, name: str) -> list[Zone]:
        result: list[Zone] = []
        for conn in self._adjacency[name]:
            zone = self.zones[conn.other(name)]
            if zone.zone_type.is_passable:
                result.append(zone)
        return result

    def get_connection(self, a: str, b: str) -> Connection:
        """Return the connection between two zones, in either order."""
        return self.connections[frozenset((a, b))]
