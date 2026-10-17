"""Entry point for the Fly-in drone routing simulation."""

import os
import sys

from flyin.colors import Palette
from flyin.errors import ParseError, UnsolvableError
from flyin.network import Network
from flyin.parser import MapParser
from flyin.plan import Plan
from flyin.planner import Planner
from flyin.renderer import TerminalRenderer
from flyin.simulation import Simulation


def solve(network: Network) -> Plan:
    """Compute a plan for all the drones of the network."""
    return Planner(network).plan()


def main() -> None:
    """Run the program with the map path given on the command line."""
    if len(sys.argv) != 2:
        print("Usage: python3 main.py <map_file>", file=sys.stderr)
        sys.exit(1)
    try:
        network = MapParser().parse(sys.argv[1])
        plan = solve(network)
    except (ParseError, UnsolvableError) as error:
        print(f"Error: {error}", file=sys.stderr)
        sys.exit(1)
    except Exception as error:
        print(f"Unexpected error: {error}", file=sys.stderr)
        sys.exit(2)
    simulation = Simulation(network, plan)
    violations = simulation.validate()
    if violations:
        print("Internal error: the computed plan is invalid:",
              file=sys.stderr)
        for violation in violations:
            print(f"  {violation}", file=sys.stderr)
        sys.exit(2)
    use_color = sys.stdout.isatty() and "NO_COLOR" not in os.environ
    TerminalRenderer(network, Palette(use_color)).render(simulation)


if __name__ == "__main__":
    main()
