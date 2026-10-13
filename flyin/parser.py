"""Parser for Fly-in map files."""

from flyin.errors import ParseError
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
        lines = self._read_useful_lines(path)
        nb_drones = self._parse_nb_drones(lines[0])
        return Network(nb_drones)

    def _read_useful_lines(self, path: str) -> list[tuple[int, str]]:
        """Return (line_number, text) for every non-comment, non-blank line.

        Args:
            path: Path to the map file.

        Returns:
            A list of (original line number, stripped text) pairs.

        Raises:
            ParseError: If the file cannot be read, is not valid text
                or has no useful lines.
        """
        lines: list[tuple[int, str]] = []
        try:
            with open(path, encoding="utf-8") as file:
                for number, raw in enumerate(file, start=1):
                    text = raw.strip()
                    if not text or text.startswith("#"):
                        continue
                    lines.append((number, text))
        except FileNotFoundError:
            raise ParseError(f"File not found: {path}")
        except IsADirectoryError:
            raise ParseError(
                "The path points to a directory, "
                f"a file was expected: {path}"
            )
        except PermissionError:
            raise ParseError(f"No permission to access: {path}")
        except UnicodeDecodeError:
            raise ParseError(f"File is not valid UTF-8 text: {path}")
        except OSError as error:
            raise ParseError(f"Could not read {path}: {error}")
        if not lines:
            raise ParseError(f"No map content found in: {path}")
        return lines

    def _parse_nb_drones(self, line: tuple[int, str]) -> int:
        """Parse the nb_drones line.

        Args:
            line: A (line number, text) pair, as returned by
                _read_useful_lines.

        Returns:
            The number of drones.

        Raises:
            ParseError: If the line is malformed or the value is not a
                positive integer.
        """
        line_number, text = line

        parts = text.split(":", 1)
        if len(parts) != 2:
            raise ParseError(
                f"Expected 'nb_drones: <number>', got '{text}'", line_number
            )
        label, value = parts[0].strip(), parts[1].strip()

        if label != "nb_drones":
            raise ParseError(
                f"Expected 'nb_drones' on the first line, got '{label}'",
                line_number
            )

        try:
            count = int(value)
        except ValueError:
            raise ParseError(
                f"nb_drones must be an integer, got '{value}'", line_number
            )

        if count <= 0:
            raise ParseError(
                f"nb_drones must be positive, got {count}", line_number
            )
        return count
