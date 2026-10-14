"""The page: strokes in pad units, how the page is turned, and the area framed for saving."""
from folio_board.hexagon.driver.for_presenting_drawings import UNIT_UM

# Slate / Folio value, used until the pad reports the real one.
FALLBACK_PRESSURE_MAX = 2047
# Stroke width on paper at the lightest and the hardest pressure.
PEN_MIN_WIDTH_MM = 0.2
PEN_MAX_WIDTH_MM = 2.4
# Stroke width on paper when pressure sensitivity is off.
PEN_FIXED_WIDTH_MM = 0.8
ORIENTATIONS = ['portrait', 'landscape', 'reverse-portrait', 'reverse-landscape']


class Board:
    def __init__(self, pad_w, pad_h):
        self.pad_w, self.pad_h = pad_w, pad_h
        self.orientation = 'portrait'
        self.strokes = []
        self.current = None
        self.hover = None
        self.pressure_max = FALLBACK_PRESSURE_MAX
        self.pressure_sensitive = True
        # Area to save, as (x0, y0, x1, y1) in view units, or None for the whole page.
        self.crop = None
        self.crop_start = None
        self.crop_before = None

    @property
    def view_size(self):
        if self.orientation in ('portrait', 'reverse-portrait'):
            return self.pad_h, self.pad_w
        return self.pad_w, self.pad_h

    def to_view(self, x, y):
        # Same mapping as tuhi's exporter, so the board matches tuhi's SVGs.
        w, h = self.view_size
        if self.orientation == 'portrait':
            return w - y, x
        if self.orientation == 'reverse-portrait':
            return y, h - x
        if self.orientation == 'reverse-landscape':
            return w - x, h - y
        return x, y

    def pen(self, in_range, x, y, pressure):
        if not in_range:
            self.hover = None
            self.current = None
            return
        self.hover = (x, y)
        if pressure == 0:
            self.current = None
            return
        if self.current is None:
            self.current = []
            self.strokes.append(self.current)
        self.current.append((x, y, min(pressure / self.pressure_max, 1.0)))

    def clear(self):
        self.strokes.clear()
        self.current = None

    def undo(self):
        if self.strokes:
            self.strokes.pop()
            self.current = None

    def rotate(self):
        i = ORIENTATIONS.index(self.orientation)
        self.orientation = ORIENTATIONS[(i + 1) % len(ORIENTATIONS)]
        self.crop = None  # it framed the page as it was turned before

    def segments(self):
        """Line segments (x0, y0, x1, y1, width) in view units; a stroke's first point is a dot."""
        units_per_mm = 1000 / UNIT_UM
        min_w, max_w = PEN_MIN_WIDTH_MM * units_per_mm, PEN_MAX_WIDTH_MM * units_per_mm
        segments = []
        for stroke in self.strokes:
            prev = None
            for x, y, p in stroke:
                vx, vy = self.to_view(x, y)
                if prev is None:
                    prev = (vx, vy, p)
                # Each segment takes the mean pressure of its ends, so width changes smoothly.
                px, py, pp = prev
                if self.pressure_sensitive:
                    width = min_w + (max_w - min_w) * (p + pp) / 2
                else:
                    width = PEN_FIXED_WIDTH_MM * units_per_mm
                segments.append((px, py, vx, vy, width))
                prev = (vx, vy, p)
        return tuple(segments)

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
