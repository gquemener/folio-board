"""Driven port for the clock."""


class ForTellingTime:
    def now(self) -> float:
        """Seconds on a clock that never goes back."""
        raise NotImplementedError
