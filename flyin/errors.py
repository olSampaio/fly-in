"""Domain-specific errors for map parsing and path planning."""


class ParseError(Exception):
    """Report invalid map data, optionally with its source line."""

    def __init__(
        self,
        message: str = "Unknown parsing error",
        line: int | None = None
    ) -> None:
        """Build a readable parsing error.

        Args:
            message: Description of the invalid input.
            line: Original source line, or None for file-level errors.
        """
        self.message = message
        self.line = line
        if line is not None:
            full_message = f"line {self.line}: {self.message}"
        else:
            full_message = self.message
        super().__init__(full_message)


class UnsolvableError(Exception):
    """Raised when the map is valid but has no path to the end zone."""
