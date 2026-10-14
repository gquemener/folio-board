"""Driver port for the presenter: the person who shows the drawing, then saves or copies it."""
from dataclasses import dataclass
from typing import Optional, Protocol

# Page coordinates are pad units: 10 µm on paper.
UNIT_UM = 10
UNIT_MM = UNIT_UM / 1000

Point = tuple[float, float]
Rect = tuple[float, float, float, float]  # x0, y0, x1, y1


@dataclass(frozen=True)
class Page:
    """The page as shown, in page units: turned to the current orientation."""
    width: float
    height: float
    # Line segments (x0, y0, x1, y1, line width), in drawing order.
    segments: tuple[tuple[float, float, float, float, float], ...]
    # Area to save or copy, or None for the whole page.
    crop: Optional[Rect] = None
    # Where the pen hovers, or None when it is out of range.
    hover: Optional[Point] = None


class ForPresentingDrawings(Protocol):
    def start(self) -> None:
        """Begin listening to the pad."""

    def stop(self) -> None:
        """Stop listening to the pad."""

    def reconnect(self) -> None:
        """Drop the pad link and wait for the pad again."""

    def clear(self) -> None: ...

    def undo(self) -> None:
        """Remove the last stroke."""

    def rotate(self) -> None:
        """Turn the page a quarter turn; this drops the crop."""

    def set_pressure_sensitive(self, on: bool) -> None:
        """Vary line width with pen pressure, or draw every stroke at the same width."""

    def begin_crop(self, at: Point) -> None:
        """Start framing the area to save or copy, at a point in page units (may lie off the page)."""

    def drag_crop(self, at: Point) -> None:
        """Frame the area between where the crop began and this point."""

    def end_crop(self, is_click: bool, min_size: float) -> None:
        """Finish framing. A click outside the previous crop drops it, a click inside keeps it.
        A crop thinner than min_size page units is dropped."""

    def save(self, path: str) -> None:
        """Save the page, or its crop: SVG when path ends in .svg, PNG otherwise."""

    def copy(self) -> None:
        """Put the page, or its crop, on the clipboard."""

    def view_size(self) -> tuple[float, float]:
        """Width and height of the page as shown, in page units."""

    def page(self) -> Page: ...
