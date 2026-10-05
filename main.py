"""Entry point for the Fly-in drone routing simulation."""

import sys


def main() -> None:
    """Run the program with the map path given on the command line."""
    if len(sys.argv) != 2:
        print("Usage: python3 main.py <map_file>")
        sys.exit(1)
    print(f"ok: {sys.argv[1]}")


if __name__ == "__main__":
    main()
