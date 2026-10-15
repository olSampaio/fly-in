"""The plan: where every drone is at every turn."""


class Plan:
    """The position of every drone at every turn."""

    def __init__(self, paths: list[list[str]]) -> None:
        """Store one list of states per drone.

        Args:
            paths: paths[i][t] is the state of drone i+1 at turn t.
                Turn 0 is the start zone. A state is a zone name, or a
                connection name while the drone is in transit.
        """
        self.paths = paths

    def state_at(self, drone: int, turn: int) -> str:
        """Return the state of a drone at a turn.

        Args:
            drone: The drone index, starting at 0.
            turn: The turn number.

        Returns:
            The state at that turn. After the end of its path, the last
            state is returned.
        """

        path = self.paths[drone]
        return path[min(turn, len(path) - 1)]

    def output_lines(self) -> list[str]:
        """Return the simulation output, one line per turn.

        Returns:
            The lines, with drones that do not move omitted.
        """
        horizon = max(len(path) for path in self.paths)
        lines: list[str] = []
        for turn in range(1, horizon):
            moves = [
                f"D{drone + 1}-{self.state_at(drone, turn)}"
                for drone in range(len(self.paths))
                if self.state_at(drone, turn)
                != self.state_at(drone, turn - 1)
            ]
            lines.append(" ".join(moves))
        while lines and lines[-1] == "":
            lines.pop()
        return lines
