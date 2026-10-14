"""Driven port for the clock."""
from typing import Protocol


class ForTellingTime(Protocol):
    def now(self) -> float:
        """Seconds on a clock that never goes back."""
