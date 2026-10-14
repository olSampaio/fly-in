"""Parser for Fly-in map files."""

from flyin.errors import ParseError
from flyin.network import Network
from flyin.zone import Zone, ZoneType


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

        network = Network(nb_drones)
        for line_number, text in lines[1:]:
            prefix, separator, rest = text.partition(":")
            if separator == "":
                raise ParseError(f"Line without separator. '{text}'",
                                 line_number)
            if prefix in ("start_hub", "end_hub", "hub"):
                self._parse_zone(network, prefix, rest, line_number)
            elif prefix == "connection":
                pass                        # etapa seguinte
            else:
                raise ParseError(f"Unknown line type. Expected: 'start_hub', "
                                 f"'end_hub', 'hub', 'connection'. Got "
                                 f"'{text}'", line_number)
        if network.start is None:
            raise ParseError("Missing start_hub")
        if network.end is None:
            raise ParseError("Missing end_hub")
        return network

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
        count = self._to_int(value, "nb_drones", line_number)

        if count <= 0:
            raise ParseError(
                f"nb_drones must be positive, got {count}", line_number
            )
        return count

    def _parse_zone(
        self, network: Network, prefix: str, rest: str, line_number: int
    ) -> None:
        """Parse a zone line and add the zone to the network.

        Args:
            network: The network being built.
            prefix: One of 'start_hub', 'end_hub' or 'hub'.
            rest: The text after the colon.
            line_number: The line number in the map file.

        Raises:
            ParseError: If the line is malformed.
        """

        core, metadata = self._split_metadata(rest, line_number)
        name, x, y = self._parse_core(core, line_number)
        pairs = self._parse_pairs(
            metadata, {"zone", "color", "max_drones"}, line_number
        )
        is_start = prefix == "start_hub"
        is_end = prefix == "end_hub"

        zone_type = self._parse_zone_type(
            pairs.get("zone", "normal"), line_number
        )
        color = pairs.get("color")

        max_drones = 1
        if "max_drones" in pairs and not (is_start or is_end):
            max_drones = self._to_int(
                pairs["max_drones"], "max_drones", line_number
            )
            if max_drones <= 0:
                raise ParseError(
                    f"max_drones must be positive, got {max_drones}",
                    line_number
                )

        if is_start and network.start is not None:
            raise ParseError(
                f"Duplicate start_hub (already defined: "
                f"'{network.start.name}')", line_number
            )
        if is_end and network.end is not None:
            raise ParseError(
                f"Duplicate end_hub (already defined: "
                f"'{network.end.name}')", line_number
            )

        zone = Zone(
            name, x, y, zone_type, color, max_drones, is_start, is_end
        )
        try:
            network.add_zone(zone)
        except ValueError as error:
            raise ParseError(str(error), line_number)

    def _parse_zone_type(self, text: str, line_number: int) -> ZoneType:
        """Convert the text of a 'zone=' value into a ZoneType.

        Args:
            text: The zone type as written in the map file.
            line_number: The line number in the map file.

        Returns:
            The matching ZoneType.

        Raises:
            ParseError: If the text is not a valid zone type.
        """
        try:
            return ZoneType(text)
        except ValueError:
            valid = ", ".join(member.value for member in ZoneType)
            raise ParseError(
                f"Unknown zone type '{text}'. Valid types: {valid}",
                line_number
            )

    def _split_metadata(
        self, text: str, line_number: int
    ) -> tuple[str, str]:
        """Split a line body into its core and its metadata text.

        Args:
            text: The text after the colon, e.g. 'roof1 3 4 [color=red]'.
            line_number: The line number in the map file.

        Returns:
            A pair (core, metadata). Metadata is an empty string when
            the line has no brackets.

        Raises:
            ParseError: If the brackets are malformed.
        """

        core, bracket, tail = text.partition("[")
        if bracket == "":
            return core.strip(), ""
        if not tail.endswith("]"):
            raise ParseError(f"Invalid metadata syntax: '{text}'", line_number)
        metadata = tail[:-1].strip()

        if "[" in metadata or "]" in metadata:
            raise ParseError("Unexpected bracket in metadata.", line_number)

        return (core.strip(), metadata)

    def _parse_core(
        self, core: str, line_number: int
    ) -> tuple[str, int, int]:
        """Parse the 'name x y' part of a zone line.

        Args:
            core: The zone text without metadata, e.g. 'roof1 3 4'.
            line_number: The line number in the map file.

        Returns:
            A tuple (name, x, y).

        Raises:
            ParseError: If the core is malformed.
        """

        parts = core.split()
        if len(parts) != 3:
            raise ParseError(
                f"Expected 'name x y', got '{core}'", line_number
            )
        name, x_text, y_text = parts
        if "-" in name:
            raise ParseError(f"Invalid name: '{name}', the name cannot "
                             "contain '-'", line_number)
        x = self._to_int(x_text, "x", line_number)
        y = self._to_int(y_text, "y", line_number)
        return (name, x, y)

    def _to_int(self, value: str, field: str, line_number: int) -> int:
        """Convert text to an integer, or raise a ParseError.

        Only an optional leading '-' followed by ASCII digits is
        accepted, so '+4' and '1_0' are rejected.

        Args:
            value: The text to convert.
            field: The field name, used in the error message.
            line_number: The line number in the map file.

        Returns:
            The converted integer.

        Raises:
            ParseError: If the text is not a valid integer.
        """

        digits = value[1:] if value.startswith("-") else value

        if not (digits.isascii() and digits.isdigit()):
            raise ParseError(
                f"The value of {field} is not an int: '{value}'",
                line_number
            )
        return int(value)

    def _parse_pairs(
        self, text: str, allowed: set[str], line_number: int
    ) -> dict[str, str]:
        """Parse 'key=value' tokens into a dictionary.

        Args:
            text: The metadata text, e.g. 'zone=restricted color=red'.
            allowed: The keys that are accepted.
            line_number: The line number in the map file.

        Returns:
            A dictionary mapping each key to its value, as text.

        Raises:
            ParseError: If a token is malformed, a key is unknown or a
                key is repeated.
        """
        result: dict[str, str] = {}
        for token in text.split():
            key, separator, value = token.partition("=")
            if separator == "":
                raise ParseError(
                    f"Expected 'key=value', got '{token}'", line_number
                )
            if not key or not value:
                raise ParseError(
                    f"Empty key or value in '{token}'", line_number
                )
            if "=" in value:
                raise ParseError(
                    f"Unexpected '=' in '{token}'", line_number
                )
            if key not in allowed:
                raise ParseError(
                    f"Unknown key '{key}'. Allowed: "
                    f"{', '.join(sorted(allowed))}", line_number
                )
            if key in result:
                raise ParseError(f"Duplicate key '{key}'", line_number)
            result[key] = value
        return result
