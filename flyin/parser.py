"""Parser for Fly-in map files."""

from flyin.network import Network


class MapParser:
    """Reads a map file and builds the corresponding Network."""

    def parse(self, path: str) -> Network:
        """Parse the map file at the given path.

        Args:
            path: Path to the map file.

        Returns:
            The Network described by the file.

        Raises:
            ParseError: If the file cannot be read or is invalid.
        """
        # 1. Get the useful lines (with their original line numbers).
        # 2. Read nb_drones from the first useful line.
        # 3. Build the Network (later steps: zones, connections, checks).
        raise NotImplementedError

    def _read_useful_lines(self, path: str) -> list[tuple[int, str]]:
        """Return (line_number, text) for every non-comment, non-blank line.

        Args:
            path: Path to the map file.

        Returns:
            A list of (original line number, stripped text) pairs.

        Raises:
            ParseError: If the file does not exist, cannot be opened or
                has no useful lines.
        """
        # open the file with a context manager
        # loop with enumerate, keeping the ORIGINAL line number
        # skip blank lines and comments
        raise NotImplementedError