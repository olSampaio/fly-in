"""Simulation: replays a plan turn by turn."""

from dataclasses import dataclass

from flyin.network import Network
from flyin.plan import Plan
from flyin.validator import Validator


@dataclass(frozen=True)
class Move:
    """One drone movement during a turn."""

    drone: int
    state: str
    zone: str

    @property
    def text(self) -> str:
        """Return the movement as written in the output (D<id>-<state>)."""
        return f"D{self.drone}-{self.state}"


@dataclass(frozen=True)
class Turn:
    """What happens during one simulation turn."""

    number: int
    moves: list[Move]
    delivered: int


class Simulation:
    """Replays a plan on a network, turn by turn."""

    def __init__(self, network: Network, plan: Plan) -> None:
        """Keep the network and the plan.

        Args:
            network: The network the plan was computed for.
            plan: The plan to replay.

        Raises:
            ValueError: If the network has no end zone.
        """
        if network.end is None:
            raise ValueError("The network needs an end zone")
        self.network = network
        self.plan = plan
        self.end = network.end

    def validate(self) -> list[str]:
        """Check the plan against the rules of the subject.

        Returns:
            The list of violations. An empty list means a valid plan.
        """
        return Validator(self.network).validate(self.plan)

    def turns(self) -> list[Turn]:
        """Replay the plan.

        Returns:
            One Turn per simulation turn, with the drones that moved.
        """
        zones = self.network.zones
        result: list[Turn] = []
        for number in range(1, len(self.plan.output_lines()) + 1):
            moves: list[Move] = []
            delivered = 0
            for drone in range(len(self.plan.paths)):
                before = self.plan.state_at(drone, number - 1)
                now = self.plan.state_at(drone, number)
                if now != before:
                    zone = now
                    if now not in zones:
                        zone = self.plan.state_at(drone, number + 1)
                    moves.append(Move(drone + 1, now, zone))
                if now == self.end.name:
                    delivered += 1
            result.append(Turn(number, moves, delivered))
        return result
