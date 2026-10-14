"""Driven port for the pad: the application asks it to stream pen input, or to stop."""
from typing import Protocol


class PadLinkError(Exception):
    def __init__(self, code: int):
        super().__init__(f'pad link failed ({code})')
        self.code = code


class ForLinkingThePad(Protocol):
    def start_live(self) -> None:
        """Wait for the pad and stream its pen input; raises PadLinkError if that cannot start."""

    def stop_live(self) -> None: ...
