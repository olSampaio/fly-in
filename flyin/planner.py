"""Planner: routes all the drones, one after the other."""

import heapq
from collections.abc import Iterator

from flyin.network import Network
from flyin.pathfinder import Pathfinder
from flyin.plan import Plan
from flyin.reservations import ReservationTable
from flyin.zone import ZoneType


class Planner:
    """Plans every drone avoiding what the previous drones reserved."""

    def __init__(self, network: Network) -> None:
        """Keep the network and its start and end zones.

        Args:
            network: The network to plan on.

        Raises:
            ValueError: If the network has no start or no end zone.
        """
        if network.start is None or network.end is None:
            raise ValueError("The network needs a start and an end zone")
        self.network = network
        self.start = network.start
        self.end = network.end
        self.horizon = 0

    def plan(self) -> Plan:
        """Plan all the drones.

        Returns:
            A valid plan for every drone of the network.

        Raises:
            UnsolvableError: If the end zone cannot be reached.
        """
        pathfinder = Pathfinder(self.network)
        duration = len(pathfinder.to_states(pathfinder.shortest_path())) - 1
        self.horizon = (self.network.nb_drones + 1) * duration
        table = ReservationTable(self.network)
        paths: list[list[str]] = []
        for _ in range(self.network.nb_drones):
            states = self._find_path(table)
            table.reserve(states)
            paths.append(states)
        return Plan(paths)

    def _find_path(self, table: ReservationTable) -> list[str]:
        """Find the earliest way to the end that respects the table.

        The search runs over (zone, turn) pairs. Among the ways that
        arrive at the same turn, the one crossing more priority zones
        wins.
        """
        start = (self.start.name, 0)
        best: dict[tuple[str, int], int] = {start: 0}
        previous: dict[tuple[str, int], tuple[str, int]] = {}
        heap: list[tuple[int, int, str]] = [(0, 0, self.start.name)]
        while heap:
            turn, score, name = heapq.heappop(heap)
            if score > best[(name, turn)]:
                continue
            if name == self.end.name:
                return self._rebuild(previous, (name, turn))
            for target, arrival, bonus in self._moves(table, name, turn):
                key = (target, arrival)
                if key not in best or score - bonus < best[key]:
                    best[key] = score - bonus
                    previous[key] = (name, turn)
                    heapq.heappush(heap, (arrival, score - bonus, target))
        raise RuntimeError("No schedule found within the horizon")

    def _moves(
        self, table: ReservationTable, name: str, turn: int
    ) -> Iterator[tuple[str, int, int]]:
        """Yield (zone, arrival turn, priority bonus) reachable from a zone."""
        if turn >= self.horizon:
            return
        zone = self.network.zones[name]
        if table.zone_has_room(zone, turn + 1):
            yield name, turn + 1, 0
        for target in self.network.neighbours(name):
            conn = self.network.get_connection(name, target.name)
            if not table.link_has_room(conn, turn + 1):
                continue
            if target.zone_type is ZoneType.RESTRICTED:
                if table.zone_has_room(target, turn + 2):
                    yield target.name, turn + 2, 0
            elif table.zone_has_room(target, turn + 1):
                bonus = 1 if target.zone_type is ZoneType.PRIORITY else 0
                yield target.name, turn + 1, bonus

    def _rebuild(
        self,
        previous: dict[tuple[str, int], tuple[str, int]],
        last: tuple[str, int],
    ) -> list[str]:
        """Turn the chain of (zone, turn) pairs into one state per turn."""
        chain = [last]
        while chain[-1] in previous:
            chain.append(previous[chain[-1]])
        chain.reverse()
        states = [chain[0][0]]
        for (origin, before), (target, after) in zip(chain, chain[1:]):
            if after - before == 2:
                states.append(f"{origin}-{target}")
            states.append(target)
        return states
