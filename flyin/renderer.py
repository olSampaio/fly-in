"""Renderer: shows the simulation in the terminal."""

import sys

from flyin.colors import Palette
from flyin.network import Network
from flyin.simulation import Move, Simulation


class TerminalRenderer:
    """Prints the simulation in the output format of the subject."""

    def __init__(self, network: Network, palette: Palette) -> None:
        """Keep the network and the palette.

        Args:
            network: The network, used to find the colour of each zone.
            palette: The palette that paints the text.
        """
        self.network = network
        self.palette = palette

    def render(self, simulation: Simulation) -> None:
        """Print one line per turn on stdout, then a summary on stderr.

        Args:
            simulation: The simulation to show.
        """
        turns = simulation.turns()
        for turn in turns:
            print(" ".join(self._paint(move) for move in turn.moves))
        sys.stdout.flush()
        delivered = turns[-1].delivered if turns else 0
        print(
            f"Done: {len(turns)} turns, {delivered} drones delivered",
            file=sys.stderr,
        )

    def _paint(self, move: Move) -> str:
        """Colour a movement with the colour of its destination zone."""
        zone = self.network.zones.get(move.zone)
        color = zone.color if zone is not None else None
        return self.palette.paint(move.text, color)
