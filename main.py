"""Entry point for the Fly-in drone routing simulation."""

import sys
from flyin.errors import ParseError
from flyin.parser import MapParser


def main() -> None:
    """Run the program with the map path given on the command line."""
    if len(sys.argv) != 2:
        print("Usage: python3 main.py <map_file>", file=sys.stderr)
        sys.exit(1)
    try:
        network = MapParser().parse(sys.argv[1])
    except ParseError as error:
        print(f"Error: {error}", file=sys.stderr)
        sys.exit(1)
    except Exception as error:
        print(f"Unexpected error: {error}", file=sys.stderr)
        sys.exit(2)
    print(f"drones: {network.nb_drones}")


if __name__ == "__main__":
    main()
