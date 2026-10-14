"""Driver port for the presenter: the person who shows the drawing, then saves or copies it."""
from dataclasses import dataclass
from typing import Optional

# Page coordinates are pad units: 10 µm on paper.
UNIT_UM = 10
UNIT_MM = UNIT_UM / 1000

Point = tuple[float, float]
Rect = tuple[float, float, float, float]  # x0, y0, x1, y1
Color = tuple[float, float, float]  # red, green, blue, from 0 to 1


@dataclass(frozen=True)
class Swatch:
    """One box of the palette strip: tapping it with the pen picks its color."""
    rect: Rect
    color: Color
    name: str
    selected: bool


@dataclass(frozen=True)
class Page:
    """The page as shown, in page units: turned to the current orientation."""
    width: float
    height: float
    # Line segments (x0, y0, x1, y1, line width, color), in drawing order.
    segments: tuple[tuple[float, float, float, float, float, Color], ...]
    # Area to save or copy, or None for the whole page.
    crop: Optional[Rect] = None
    # Where the pen hovers, or None when it is out of range.
    hover: Optional[Point] = None
    # The palette strip along the pad's top edge. It is not part of the drawing.
    palette: tuple[Swatch, ...] = ()


class ForPresentingDrawings:
    def start(self) -> None:
        """Bring back the drawing kept from the last session, then begin listening to the pad."""
        raise NotImplementedError

    def stop(self) -> None:
        """Stop listening to the pad."""
        raise NotImplementedError

    def reconnect(self) -> None:
        """Drop the pad link and wait for the pad again."""
        raise NotImplementedError

    def clear(self) -> None:
        """Remove every stroke, from the drawing kept between sessions too."""
        raise NotImplementedError

    def undo(self) -> None:
        """Remove the last stroke."""
        raise NotImplementedError

    def rotate(self) -> None:
        """Turn the page a quarter turn; this drops the crop."""
        raise NotImplementedError

    def set_pressure_sensitive(self, on: bool) -> None:
        """Vary line width with pen pressure, or draw every stroke at the same width."""
        raise NotImplementedError

    def begin_crop(self, at: Point) -> None:
        """Start framing the area to save or copy, at a point in page units (may lie off the page)."""
        raise NotImplementedError

    def drag_crop(self, at: Point) -> None:
        """Frame the area between where the crop began and this point."""
        raise NotImplementedError

    def end_crop(self, is_click: bool, min_size: float) -> None:
        """Finish framing. A click outside the previous crop drops it, a click inside keeps it.
        A crop thinner than min_size page units is dropped."""
        raise NotImplementedError

    def save(self, path: str) -> None:
        """Save the page, or its crop: SVG when path ends in .svg, PNG otherwise."""
        raise NotImplementedError

    def copy(self) -> None:
        """Put the page, or its crop, on the clipboard."""
        raise NotImplementedError

    def view_size(self) -> tuple[float, float]:
        """Width and height of the page as shown, in page units."""
        raise NotImplementedError

    def page(self) -> Page:
        raise NotImplementedError
