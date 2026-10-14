"""The page: strokes and shapes in pad units, how the page is turned, and the area framed for saving."""
from folio_board.hexagon import palette, shapes
from folio_board.hexagon.driven.for_remembering_the_drawing import Item, Stroke
from folio_board.hexagon.driver.for_presenting_drawings import UNIT_UM, Orientation, Swatch

# Slate / Folio value, used until the pad reports the real one.
FALLBACK_PRESSURE_MAX = 2047
# Stroke width on paper at the lightest and the hardest pressure.
PEN_MIN_WIDTH_MM = 0.2
PEN_MAX_WIDTH_MM = 2.4
# Stroke width on paper when pressure sensitivity is off.
PEN_FIXED_WIDTH_MM = 0.8
STRIP_TOP_UNITS = palette.STRIP_TOP_MM * 1000 // UNIT_UM
STRIP_BOTTOM_UNITS = STRIP_TOP_UNITS + palette.STRIP_MM * 1000 // UNIT_UM


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
        self.color = 0
        # The pen went down on the palette strip and has not been lifted since.
        self.picking = False
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
        return w - x, h - y  # landscape: the pad's top edge, and the palette strip, on the right

    def pen(self, in_range, x, y, pressure):
        """Follow the pen; True when it just picked a color on the palette strip."""
        if not in_range or pressure == 0:
            self.hover = (x, y) if in_range else None
            self.current = None
            self.picking = False
            return False
        self.hover = (x, y)
        if self.picking:
            return False  # wait for the pen to lift, so a slide off the strip draws nothing
        if self.current is None:
            swatch = self.swatch_at(x, y)
            if swatch is not None:
                self.color = swatch
                self.picking = True
                return True
            self.current = Stroke(self.color)
            self.items.append(self.current)
        self.current.points.append((x, y, min(pressure / self.pressure_max, 1.0)))
        return False

    def to_portrait(self, x, y):
        """Pad units to the page as shown in portrait, where the palette strip is along the top."""
        return self.pad_h - y, x

    def swatch_at(self, x, y):
        """Index of the palette color under pad point (x, y), or None off the strip."""
        px, py = self.to_portrait(x, y)
        if not (STRIP_TOP_UNITS <= py < STRIP_BOTTOM_UNITS and 0 <= px <= self.pad_h):
            return None
        return min(int(px * len(palette.COLORS) // self.pad_h), len(palette.COLORS) - 1)

    def swatches(self):
        """The palette strip's boxes, in view units."""
        n = len(palette.COLORS)
        swatches = []
        for i, (name, value) in enumerate(palette.COLORS):
            # Box i spans portrait x from i/n to (i+1)/n of the strip: pad y counts the other way.
            (ax, ay) = self.to_view(STRIP_TOP_UNITS, self.pad_h * (n - i) / n)
            (bx, by) = self.to_view(STRIP_BOTTOM_UNITS, self.pad_h * (n - i - 1) / n)
            rect = (min(ax, bx), min(ay, by), max(ax, bx), max(ay, by))
            swatches.append(Swatch(rect, palette.rgb(value), name, i == self.color))
        return tuple(swatches)

    def replace(self, strokes, shape):
        """Put shape where the first of these strokes was, and drop them."""
        at = next(i for i, item in enumerate(self.items) if item is strokes[0])
        self.items[at:at] = [shape]
        self.items = [item for item in self.items if not any(item is s for s in strokes)]

    def clear(self):
        self.items.clear()
        self.sketches.clear()
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
