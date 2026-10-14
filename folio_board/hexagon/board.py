"""The page: strokes and shapes in pad units, how the page is turned, and the area framed for saving."""
import math

from folio_board.hexagon import palette, shapes
from folio_board.hexagon.driven.for_remembering_the_drawing import Item, Stroke
from folio_board.hexagon.driver.for_presenting_drawings import UNIT_UM, Orientation, PenColor

# Slate / Folio value, used until the pad reports the real one.
FALLBACK_PRESSURE_MAX = 2047
# Stroke width on paper at the lightest and the hardest pressure.
PEN_MIN_WIDTH_MM = 0.2
PEN_MAX_WIDTH_MM = 2.4
# Stroke width on paper when pressure sensitivity is off.
PEN_FIXED_WIDTH_MM = 0.8
# The eraser takes away what passes within this distance of the pen.
ERASER_MM = 2.5


class Board:
    def __init__(self, pad_w, pad_h):
        self.pad_w, self.pad_h = pad_w, pad_h
        self.orientation: Orientation = 'portrait'
        self.items: list[Item] = []  # strokes and shapes, in drawing order
        self.sketches = {}  # id(shape): (shape, its sketched lines with their taper), worked out once
        self.current = None
        self.hover = None
        self.pressure_max = FALLBACK_PRESSURE_MAX
        self.pressure_sensitive = True
        self.color = 0  # index in palette.COLORS
        self.erasing = False
        self.eraser_at = None  # where the pen last touched the paper while erasing
        self.bounds = {}  # id(item): (item, its bounding box in pad units), worked out once
        # Area to save, as (x0, y0, x1, y1) in view units, or None for the whole page.
        self.crop = None
        self.crop_start = None
        self.crop_before = None

    @property
    def view_size(self):
        if self.orientation == 'portrait':
            return self.pad_h, self.pad_w
        return self.pad_w, self.pad_h

    def to_view(self, x, y):
        # Same mapping as tuhi's exporter, so the board matches tuhi's SVGs.
        w, h = self.view_size
        if self.orientation == 'portrait':
            return w - y, x
        return w - x, h - y  # landscape: the pad's top edge on the right

    def pen(self, in_range, x, y, pressure):
        """Follow the pen; True when it erased something."""
        if not in_range or pressure == 0:
            self.hover = (x, y) if in_range else None
            self.current = None
            self.eraser_at = None
            return False
        self.hover = (x, y)
        if self.erasing:
            # Erase along the way from the last report, so a quick swipe misses nothing.
            start, self.eraser_at = self.eraser_at or (x, y), (x, y)
            return self.erase(start, (x, y))
        if self.current is None:
            self.current = Stroke(self.color)
            self.items.append(self.current)
        self.current.points.append((x, y, min(pressure / self.pressure_max, 1.0)))
        return False

    def erase(self, a, b):
        """Take away every item that passes within ERASER_MM of the segment from a to b."""
        reach = ERASER_MM * 1000 / UNIT_UM
        x0, y0 = min(a[0], b[0]) - reach, min(a[1], b[1]) - reach
        x1, y1 = max(a[0], b[0]) + reach, max(a[1], b[1]) + reach
        kept = []
        for item in self.items:
            ix0, iy0, ix1, iy1 = self.bounds_of(item)
            near = ix0 <= x1 and x0 <= ix1 and iy0 <= y1 and y0 <= iy1
            if not (near and any(segment_distance(a, b, p, q) <= reach for p, q in self.lines_of(item))):
                kept.append(item)
        erased = len(kept) < len(self.items)
        self.items = kept
        return erased

    def lines_of(self, item):
        """The item's line segments, in pad units: a stroke of a single point is a dot."""
        if isinstance(item, Stroke):
            points = [p[:2] for p in item.points]
            return zip(points, points[1:] or points)
        return ((p, q) for line, _ in self.sketch(item) for p, q in zip(line, line[1:]))

    def bounds_of(self, item):
        cached = self.bounds.get(id(item))
        if cached is None or cached[0] is not item:
            points = [p for segment in self.lines_of(item) for p in segment]
            xs, ys = [p[0] for p in points], [p[1] for p in points]
            cached = self.bounds[id(item)] = (item, (min(xs), min(ys), max(xs), max(ys)))
        return cached[1]

    def pen_color(self):
        name, value = palette.COLORS[self.color]
        return PenColor(name, palette.rgb(value))

    def eraser_reach(self):
        """How far the eraser reaches, in view units, or None when the pen draws."""
        return ERASER_MM * 1000 / UNIT_UM if self.erasing else None

    def replace(self, strokes, shape):
        """Put shape where the first of these strokes was, and drop them."""
        at = next(i for i, item in enumerate(self.items) if item is strokes[0])
        self.items[at:at] = [shape]
        self.items = [item for item in self.items if not any(item is s for s in strokes)]

    def clear(self):
        self.items.clear()
        self.sketches.clear()
        self.bounds.clear()
        self.current = None

    def set_orientation(self, orientation: Orientation):
        if orientation != self.orientation:
            self.orientation = orientation
            self.crop = None  # it framed the page as it was turned before

    def width(self, pressure):
        """Line width in pad units for a pressure from 0 to 1."""
        units_per_mm = 1000 / UNIT_UM
        if not self.pressure_sensitive:
            return PEN_FIXED_WIDTH_MM * units_per_mm
        return (PEN_MIN_WIDTH_MM + (PEN_MAX_WIDTH_MM - PEN_MIN_WIDTH_MM) * pressure) * units_per_mm

    def segments(self):
        """Line segments (x0, y0, x1, y1, width, color) in view units; a stroke's first point is a dot."""
        segments = []
        for item in self.items:
            color = palette.rgb(palette.COLORS[item.color][1])
            if not isinstance(item, Stroke):
                width = self.width(item.pressure)
                for line, taper in self.sketch(item):
                    view = [self.to_view(x, y) for x, y in line]
                    segments += [(*a, *b, width * t, color) for a, b, t in zip(view, view[1:], taper)]
                continue
            prev = None
            for x, y, p in item.points:
                vx, vy = self.to_view(x, y)
                if prev is None:
                    prev = (vx, vy, p)
                # Each segment takes the mean pressure of its ends, so width changes smoothly.
                px, py, pp = prev
                segments.append((px, py, vx, vy, self.width((p + pp) / 2), color))
                prev = (vx, vy, p)
        return tuple(segments)

    def sketch(self, shape):
        cached = self.sketches.get(id(shape))
        if cached is None or cached[0] is not shape:
            cached = self.sketches[id(shape)] = (shape, [(line, shapes.taper(line)) for line in shapes.sketch(shape)])
        return cached[1]

    def clamp(self, x, y):
        vw, vh = self.view_size
        return min(max(x, 0), vw), min(max(y, 0), vh)

    def begin_crop(self, at):
        self.crop_start = at
        self.crop_before = self.crop

    def drag_crop(self, at):
        if self.crop_start is None:
            return
        (ax, ay), (bx, by) = self.clamp(*self.crop_start), self.clamp(*at)
        self.crop = (min(ax, bx), min(ay, by), max(ax, bx), max(ay, by))

    def end_crop(self, is_click, min_size):
        if self.crop_start is None:
            return
        crop = self.crop
        if is_click:
            # A click keeps the crop it lands in and drops it anywhere else.
            px, py = self.crop_start
            before = self.crop_before
            inside = before and before[0] <= px <= before[2] and before[1] <= py <= before[3]
            self.crop = before if inside else None
        elif crop and min(crop[2] - crop[0], crop[3] - crop[1]) < min_size:
            self.crop = None  # dragged along a page edge, nothing left to frame
        self.crop_start = self.crop_before = None


def segment_distance(a, b, c, d):
    """Shortest distance between segments ab and cd."""
    def side(p, q, r):
        return (q[0] - p[0]) * (r[1] - p[1]) - (q[1] - p[1]) * (r[0] - p[0])
    if (side(a, b, c) * side(a, b, d) < 0) and (side(c, d, a) * side(c, d, b) < 0):
        return 0.0  # they cross
    return min(point_segment_distance(a, c, d), point_segment_distance(b, c, d),
               point_segment_distance(c, a, b), point_segment_distance(d, a, b))


def point_segment_distance(p, a, b):
    dx, dy = b[0] - a[0], b[1] - a[1]
    length2 = dx * dx + dy * dy
    t = 0 if length2 == 0 else max(0, min(1, ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / length2))
    return math.hypot(p[0] - a[0] - t * dx, p[1] - a[1] - t * dy)
