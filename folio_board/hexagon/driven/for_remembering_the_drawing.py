"""Driven port for keeping the drawing from one session to the next."""
from dataclasses import dataclass, field


@dataclass
class Stroke:
    color: int  # index in palette.COLORS
    points: list = field(default_factory=list)  # (x, y, pressure from 0 to 1), in pad units


class RememberingError(Exception):
    pass


class ForRememberingTheDrawing:
    def remember(self, strokes: list[Stroke]) -> None:
        """Keep these strokes in place of the ones kept before; raises RememberingError."""
        raise NotImplementedError

    def recall(self) -> list[Stroke]:
        """The strokes kept last, or none if nothing was kept; raises RememberingError."""
        raise NotImplementedError
