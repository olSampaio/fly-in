"""Validator: checks a plan against the rules of the subject."""

from flyin.connection import Connection
from flyin.network import Network
from flyin.plan import Plan
from flyin.zone import ZoneType


class Validator:
    """Checks that a plan respects every movement and capacity rule."""

    def __init__(self, network: Network) -> None:
        """Keep the network and its start and end zones.

        Args:
            network: The network the plan was computed for.

        Raises:
            ValueError: If the network has no start or no end zone.
        """
        if network.start is None or network.end is None:
            raise ValueError("The network needs a start and an end zone")
        self.network = network
        self.start = network.start
        self.end = network.end

    def validate(self, plan: Plan) -> list[str]:
        """Check a plan and return all detected violations."""
        errors: list[str] = []
        self._check_endpoints(plan, errors)

        if not plan.paths or any(not path for path in plan.paths):
            return errors

        self._check_moves(plan, errors)
        self._check_capacity(plan, errors)
        return errors

    def _check_endpoints(self, plan: Plan, errors: list[str]) -> None:
        """Check the number of drones, their start and their end."""
        if len(plan.paths) != self.network.nb_drones:
            errors.append(
                f"Plan has {len(plan.paths)} drones, "
                f"expected {self.network.nb_drones}"
            )

        for drone, path in enumerate(plan.paths):
            if not path:
                errors.append(f"D{drone + 1} has an empty path")
                continue

            if path[0] != self.start.name:
                errors.append(
                    f"D{drone + 1} starts at '{path[0]}', "
                    f"expected '{self.start.name}'"
                )

            if path[-1] != self.end.name:
                errors.append(
                    f"D{drone + 1} ends at '{path[-1]}', "
                    f"expected '{self.end.name}'"
                )

    def _connection_of(self, state: str) -> Connection | None:
        """Return the connection named by a state, if it is one."""
        names = state.split("-")
        if len(names) != 2:
            return None
        return self.network.connections.get(frozenset(names))

    def _check_moves(self, plan: Plan, errors: list[str]) -> None:
        """Check that every transition between two turns is legal."""
        zones = self.network.zones
        for drone, path in enumerate(plan.paths):
            for turn in range(1, len(path)):
                prev, cur = path[turn - 1], path[turn]
                where = f"Turn {turn}: D{drone + 1}"
                if prev == self.end.name and cur != prev:
                    errors.append(f"{where} leaves the end zone")
                elif prev in zones:
                    self._check_from_zone(prev, cur, where, errors)
                elif self._connection_of(prev) is not None:
                    self._check_arrival(path, turn, where, errors)
                else:
                    errors.append(f"{where} was in unknown state '{prev}'")

    def _check_from_zone(
        self, prev: str, cur: str, where: str, errors: list[str]
    ) -> None:
        """Check a transition that starts from a zone."""
        zones = self.network.zones
        if cur == prev:
            return
        if cur in zones:
            if frozenset((prev, cur)) not in self.network.connections:
                errors.append(f"{where} moves {prev} -> {cur}: no connection")
            elif zones[cur].zone_type is ZoneType.BLOCKED:
                errors.append(f"{where} enters blocked zone '{cur}'")
            elif zones[cur].zone_type is ZoneType.RESTRICTED:
                errors.append(
                    f"{where} enters restricted zone '{cur}' in one turn"
                )
            return
        conn = self._connection_of(cur)
        if conn is None:
            errors.append(f"{where} moves to unknown state '{cur}'")
        elif prev not in (conn.zone_a, conn.zone_b):
            errors.append(f"{where} enters '{cur}' from '{prev}'")
        elif cur != f"{prev}-{conn.other(prev)}":
            errors.append(
                f"{where} uses a connection name in the wrong direction"
            )
        elif zones[conn.other(prev)].zone_type is not ZoneType.RESTRICTED:
            errors.append(
                f"{where} is in flight toward a zone that is not restricted"
            )

    def _check_arrival(
        self, path: list[str], turn: int, where: str, errors: list[str]
    ) -> None:
        """Check that a drone in flight arrives at its destination."""
        conn = self._connection_of(path[turn - 1])
        if conn is None or turn < 2:
            return
        origin = path[turn - 2]
        if origin not in self.network.zones:
            return
        destination = conn.other(origin)
        if path[turn] != destination:
            errors.append(
                f"{where} must arrive at '{destination}', "
                f"found '{path[turn]}'"
            )

    def _link_used(self, prev: str, cur: str) -> frozenset[str] | None:
        """Return the connection a drone uses during a turn, if any."""
        zones = self.network.zones
        if prev not in zones or cur == prev:
            return None
        if cur in zones:
            key = frozenset((prev, cur))
            return key if key in self.network.connections else None
        conn = self._connection_of(cur)
        return conn.key if conn is not None else None

    def _check_capacity(self, plan: Plan, errors: list[str]) -> None:
        """Check zone occupancy and connection capacity, turn by turn."""
        zones = self.network.zones
        horizon = max(len(path) for path in plan.paths)
        for turn in range(1, horizon):
            in_zone: dict[str, int] = {}
            on_link: dict[frozenset[str], int] = {}
            for drone in range(len(plan.paths)):
                prev = plan.state_at(drone, turn - 1)
                cur = plan.state_at(drone, turn)
                if cur in zones:
                    in_zone[cur] = in_zone.get(cur, 0) + 1
                link = self._link_used(prev, cur)
                if link is not None:
                    on_link[link] = on_link.get(link, 0) + 1
            for name, count in in_zone.items():
                zone = zones[name]
                if zone.is_start or zone.is_end:
                    continue
                if count > zone.max_drones:
                    errors.append(
                        f"Turn {turn}: zone '{name}' holds {count} "
                        f"drones, max is {zone.max_drones}"
                    )
            for link, count in on_link.items():
                conn = self.network.connections[link]
                if count > conn.max_link_capacity:
                    errors.append(
                        f"Turn {turn}: connection '{conn.name}' used by "
                        f"{count} drones, max is {conn.max_link_capacity}"
                    )
