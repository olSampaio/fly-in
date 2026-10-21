"""Undirected, capacity-limited connections between zones."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Connection:
    """Link two zones, sharing capacity in both travel directions."""

    zone_a: str
    zone_b: str
    max_link_capacity: int = 1

    @property
    def name(self) -> str:
        """Return the connection name in its declared endpoint order."""
        return f"{self.zone_a}-{self.zone_b}"

    @property
    def key(self) -> frozenset[str]:
        """Return an order-independent key for this connection."""
        return frozenset((self.zone_a, self.zone_b))

    def other(self, zone: str) -> str:
        """Return the opposite endpoint of a connection.

        Args:
            zone: Name of an endpoint belonging to this connection.

        Returns:
            The other endpoint. Callers must supply a valid endpoint.
        """
        return self.zone_b if zone == self.zone_a else self.zone_a
