"""Driven port for keeping the drawing from one session to the next."""
from dataclasses import dataclass, field
from typing import Union

Point = tuple[float, float]


@dataclass
class Stroke:
    color: int  # index in palette.COLORS
    points: list = field(default_factory=list)  # (x, y, pressure from 0 to 1), in pad units


@dataclass
class Box:
    """A box that replaced hand-drawn strokes, upright on the pad."""
    color: int
    pressure: float  # the strokes' mean pressure, from 0 to 1
    rect: tuple[float, float, float, float]  # x0, y0, x1, y1 in pad units
    strokes: list[Stroke]  # as drawn by hand


@dataclass
class Arrow:
    """An arrow that replaced hand-drawn strokes: a quadratic curve, straight when control is its middle."""
    color: int
    pressure: float
    tail: Point
    control: Point
    tip: Point
    strokes: list[Stroke]


Item = Union[Stroke, Box, Arrow]


class RememberingError(Exception):
    pass


class ForRememberingTheDrawing:
    def remember(self, items: list[Item]) -> None:
        """Keep these strokes and shapes in place of the ones kept before; raises RememberingError."""
        raise NotImplementedError

    def recall(self) -> list[Item]:
        """The strokes and shapes kept last, or none if nothing was kept; raises RememberingError."""
        raise NotImplementedError
