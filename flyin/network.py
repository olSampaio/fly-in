"""Storage and adjacency queries for a drone routing network."""

from flyin.connection import Connection
from flyin.zone import Zone


class Network:
    """Hold the zones, connections, and start/end hubs of a map."""

    def __init__(self, nb_drones: int) -> None:
        """Create an empty network for the requested number of drones.

        Args:
            nb_drones: Number of drones to route through the network.
        """
        self.nb_drones = nb_drones
        self.zones: dict[str, Zone] = {}
        self.connections: dict[frozenset[str], Connection] = {}
        self._adjacency: dict[str, list[Connection]] = {}
        self.start: Zone | None = None
        self.end: Zone | None = None

    def add_zone(self, zone: Zone) -> None:
        """Register a zone and initialize its adjacency list.

        Args:
            zone: The zone to insert.

        Raises:
            ValueError: If its name is already registered.
        """
        if zone.name in self.zones:
            raise ValueError(f"Duplicated zone name: {zone.name}")
        self.zones[zone.name] = zone
        self._adjacency[zone.name] = []
        if zone.is_start:
            self.start = zone
        if zone.is_end:
            self.end = zone

    def add_connection(self, conn: Connection) -> None:
        """Add an undirected connection between two existing zones.

        Args:
            conn: The connection to register.

        Raises:
            ValueError: If an endpoint is unknown or the link is duplicate.
        """
        for name in (conn.zone_a, conn.zone_b):
            if name not in self.zones:
                raise ValueError(f"Unknown name: {name}")
        if conn.key in self.connections:
            raise ValueError(f"Duplicate connection {conn.name}")
        self.connections[conn.key] = conn
        self._adjacency[conn.zone_a].append(conn)
        self._adjacency[conn.zone_b].append(conn)

    def neighbours(self, name: str) -> list[Zone]:
        """Return passable zones directly connected to the given zone.

        Args:
            name: Name of a zone already registered in the network.

        Returns:
            Adjacent zones, excluding those marked as blocked.

        Raises:
            KeyError: If the requested zone is not in the network.
        """
        result: list[Zone] = []
        for conn in self._adjacency[name]:
            zone = self.zones[conn.other(name)]
            if zone.zone_type.is_passable:
                result.append(zone)
        return result

    def get_connection(self, a: str, b: str) -> Connection:
        """Return the connection between two zones, in either order."""
        return self.connections[frozenset((a, b))]
