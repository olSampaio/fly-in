class ParseError(Exception):
    def __init__(
        self,
        message: str = "Unknown parsing error",
        line: int | None = None
    ) -> None:
        self.message = message
        self.line = line
        if line is not None:
            full_message = f"line {self.line}: {self.message}"
        else:
            full_message = self.message
        super().__init__(full_message)
