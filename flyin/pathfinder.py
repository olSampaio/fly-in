"""Pathfinding: the cheapest route for a single drone."""

import heapq

from flyin.errors import UnsolvableError
from flyin.network import Network
from flyin.plan import Plan
from flyin.zone import ZoneType


class Pathfinder:
    """Finds the cheapest route from the start to the end zone."""

    def __init__(self, network: Network) -> None:
        """Keep the network and its start and end zones.

        Args:
            network: The network to search.

        Raises:
            ValueError: If the network has no start or no end zone.
        """
        if network.start is None or network.end is None:
            raise ValueError("The network needs a start and an end zone")
        self.network = network
        self.start = network.start
        self.end = network.end

    def shortest_path(self) -> list[str]:
        """Return the zone names of the cheapest path, start to end.

        The cost is the number of turns. Among paths with the same
        number of turns, the one crossing more priority zones wins.

        Returns:
            The zone names, from the start zone to the end zone.

        Raises:
            UnsolvableError: If the end zone cannot be reached.
        """
        start = self.start.name
        best: dict[str, tuple[int, int]] = {start: (0, 0)}
        previous: dict[str, str] = {}
        heap: list[tuple[tuple[int, int], str]] = [((0, 0), start)]
        while heap:
            cost, name = heapq.heappop(heap)
            if cost > best[name]:
                continue
            if name == self.end.name:
                return self._rebuild(previous)
            turns, priority = cost
            for zone in self.network.neighbours(name):
                bonus = 1 if zone.zone_type is ZoneType.PRIORITY else 0
                new_cost = (turns + zone.zone_type.cost, priority - bonus)
                if zone.name not in best or new_cost < best[zone.name]:
                    best[zone.name] = new_cost
                    previous[zone.name] = name
                    heapq.heappush(heap, (new_cost, zone.name))
        raise UnsolvableError(
            f"No path from '{self.start.name}' to '{self.end.name}'"
        )

    def _rebuild(self, previous: dict[str, str]) -> list[str]:
        """Walk back from the end zone to the start zone."""
        path = [self.end.name]
        while path[-1] != self.start.name:
            path.append(previous[path[-1]])
        path.reverse()
        return path

    def to_states(self, path: list[str]) -> list[str]:
        """Turn a list of zones into one state per turn.

        Args:
            path: The zone names, from the start zone to the end zone.

        Returns:
            The state of the drone at each turn. Moving to a restricted
            zone adds an in-flight state named after the connection.
        """
        states = [path[0]]
        for origin, destination in zip(path, path[1:]):
            zone = self.network.zones[destination]
            if zone.zone_type is ZoneType.RESTRICTED:
                states.append(f"{origin}-{destination}")
            states.append(destination)
        return states

    def plan_for_one_drone(self) -> Plan:
        """Return the plan of a single drone along the cheapest path."""
        return Plan([self.to_states(self.shortest_path())])
