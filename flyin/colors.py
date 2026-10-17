"""ANSI colours for the terminal output."""

from typing import ClassVar


class Palette:
    """Maps colour names from the map file to ANSI escape codes."""

    CODES: ClassVar[dict[str, str]] = {
        "black": "30;47",
        "red": "31",
        "green": "32",
        "yellow": "33",
        "blue": "34",
        "magenta": "35",
        "cyan": "36",
        "white": "37",
        "gray": "90",
        "grey": "90",
        "orange": "38;5;208",
        "purple": "38;5;93",
        "violet": "38;5;177",
        "brown": "38;5;94",
        "gold": "38;5;220",
        "crimson": "38;5;161",
        "darkred": "38;5;88",
        "maroon": "38;5;52",
        "lime": "38;5;118",
    }

    def __init__(self, enabled: bool) -> None:
        """Create a palette.

        Args:
            enabled: If False, text is never coloured.
        """
        self.enabled = enabled

    def paint(self, text: str, color: str | None) -> str:
        """Return the text wrapped in the ANSI code of a colour name.

        Args:
            text: The text to colour.
            color: A colour name from the map file, or None.

        Returns:
            The coloured text, or the text unchanged if colours are
            disabled or the colour name is unknown.
        """
        if not self.enabled or color is None:
            return text
        code = self.CODES.get(color.lower())
        if code is None:
            return text
        return f"\033[{code}m{text}\033[0m"
