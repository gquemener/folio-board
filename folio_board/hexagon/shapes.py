"""Hand-drawn boxes, circles and arrows, recognized and redrawn in a sketchy mockup style.

Strokes drawn one right after another, in the same color, form a group; when a group
looks like a box, an ellipse, or an arrow (a shaft, then a head of one or two strokes),
it is replaced by that shape. All lengths are in pad units, as strokes are.

The thresholds were tuned on tests/fixtures/shape_samples.json, drawn on a Bamboo Folio.
"""
import math
import random
import statistics
from typing import Optional, Union

from folio_board.hexagon.driven.for_remembering_the_drawing import Arrow, Box, Ellipse, Stroke
from folio_board.hexagon.driver.for_presenting_drawings import UNIT_UM

MM = 1000 / UNIT_UM

# A pause longer than this between two strokes starts a new group.
GROUP_PAUSE_S = 1.5
# The most strokes a box can be drawn with; an arrow takes at most 3.
GROUP_MAX = 4
# Strokes shorter than this, like a pen touching the paper by accident, are left out of groups.
TINY_MM = 2

# A box's shorter side is at least this long, so that handwriting never snaps.
BOX_MIN_MM = 8
# How far, relative to the box's shorter side, the drawing may leave a gap along the box's outline
# or cut a corner; circles do by 0.17 or more. A tenth of the drawing may stray from the outline
# by up to twice as much.
BOX_TOLERANCE = 0.15

# An ellipse's smaller diameter is at least this long, as for boxes.
ELLIPSE_MIN_MM = 8
# How far, relative to its radius, the drawing may stray from the ellipse: most of it, and all of it.
# Boxes stray 0.25 or more at their corners.
ELLIPSE_TOLERANCE = (0.12, 0.25)
# How much of the turn around the center the drawing must cover, so that a U or an arc stays as drawn.
ELLIPSE_TURN = 0.9
# An ellipse whose radii differ by less than this, relative to the larger one, becomes a circle.
CIRCLE_ROUNDNESS = 0.2

ARROW_MIN_MM = 15
# How far the shaft may stray from a smooth curve, relative to its length.
SHAFT_TOLERANCE = 0.06
# How far the head's tip may be from the shaft's end, relative to the shaft's length.
TIP_TOLERANCE = 0.12
# Angle between each side of the head and the shaft, and their length relative to the shaft.
HEAD_ANGLES = (10, 65)
HEAD_LENGTHS = (0.1, 0.6)
# The most two strokes of a head can be apart where they meet.
HEAD_GAP_MM = 3
# A shaft bending less than this, relative to its length, is straight; a straight one within
# SNAP_DEGREES of a multiple of 45° is turned to it.
STRAIGHT_BEND = 0.05
SNAP_DEGREES = 5

Shape = Union[Box, Ellipse, Arrow]


class Grouper:
    """Follows the strokes as they end, and tells which ones together make a shape."""

    def __init__(self):
        self.recent = []  # (stroke, ended at)

    def reset(self):
        self.recent = []

    def stroke_done(self, stroke: Stroke, started: float, ended: float) -> Optional[tuple[Shape, list[Stroke]]]:
        """The shape the latest strokes make, with the strokes it replaces, or None."""
        if path_length(stroke.points) < TINY_MM * MM:
            return None
        if self.recent:
            last, last_ended = self.recent[-1]
            if started - last_ended > GROUP_PAUSE_S or stroke.color != last.color:
                self.recent = []
        self.recent = (self.recent + [(stroke, ended)])[-GROUP_MAX:]
        strokes = [s for s, _ in self.recent]
        # The most strokes first: fewer of them would have made a shape when they were drawn.
        for k in range(len(strokes), 0, -1):
            shape = recognize(strokes[-k:])
            if shape:
                self.recent = []
                return shape, strokes[-k:]
        return None


def recognize(strokes: list[Stroke]) -> Optional[Shape]:
    return box(strokes) or ellipse(strokes) or (arrow(strokes[0], strokes[1:]) if 2 <= len(strokes) <= 3 else None)


# Boxes

def box(strokes: list[Stroke]) -> Optional[Box]:
    points = resample([p for s in strokes for p in s.points], MM)
    if len(points) < 8:
        return None
    rect = fit_rect(points)
    x0, y0, x1, y1 = rect
    short = min(x1 - x0, y1 - y0)
    if short < BOX_MIN_MM * MM:
        return None
    tolerance = BOX_TOLERANCE * short
    corners = ((x0, y0), (x1, y0), (x1, y1), (x0, y1))
    strays = [distance_to_rect(p, rect) for p in points]
    if (sum(d > tolerance for d in strays) > 0.1 * len(strays) or max(strays) > 2 * tolerance
            or any(nearest(points, p) > tolerance for p in outline(rect, 100))
            or any(nearest(points, c) > tolerance for c in corners)):
        return None
    return Box(strokes[0].color, mean_pressure(strokes), rect, list(strokes))


def fit_rect(points):
    """The upright rectangle the points run along: each side sits at the median of the points nearest it."""
    xs, ys = sorted(p[0] for p in points), sorted(p[1] for p in points)
    n = len(points)
    rect = [xs[n // 20], ys[n // 20], xs[n - 1 - n // 20], ys[n - 1 - n // 20]]
    for _ in range(4):
        sides = [[], [], [], []]
        for x, y in points:
            gaps = (abs(x - rect[0]), abs(y - rect[1]), abs(x - rect[2]), abs(y - rect[3]))
            side = gaps.index(min(gaps))
            sides[side].append(x if side in (0, 2) else y)
        rect = [statistics.median(s) if s else rect[i] for i, s in enumerate(sides)]
    x0, y0, x1, y1 = rect
    return min(x0, x1), min(y0, y1), max(x0, x1), max(y0, y1)


def distance_to_rect(p, rect):
    x, y = p
    x0, y0, x1, y1 = rect
    if x0 <= x <= x1 and y0 <= y <= y1:
        return min(x - x0, x1 - x, y - y0, y1 - y)
    return math.hypot(max(x0 - x, 0, x - x1), max(y0 - y, 0, y - y1))


def outline(rect, n):
    x0, y0, x1, y1 = rect
    corners = [(x0, y0), (x1, y0), (x1, y1), (x0, y1), (x0, y0)]
    return polyline_points(corners, n)


# Ellipses

def ellipse(strokes: list[Stroke]) -> Optional[Ellipse]:
    points = resample([p for s in strokes for p in s.points], MM / 2)
    if len(points) < 16:
        return None
    # The extent of the points, leaving out the 2% furthest on each side, such as where the pen
    # ran past its starting point.
    xs, ys = sorted(p[0] for p in points), sorted(p[1] for p in points)
    n, k = len(points), len(points) // 50
    x0, x1, y0, y1 = xs[k], xs[n - 1 - k], ys[k], ys[n - 1 - k]
    cx, cy, rx, ry = (x0 + x1) / 2, (y0 + y1) / 2, (x1 - x0) / 2, (y1 - y0) / 2
    if 2 * min(rx, ry) < ELLIPSE_MIN_MM * MM:
        return None
    strays = sorted(abs(math.hypot((x - cx) / rx, (y - cy) / ry) - 1) for x, y in points)
    if strays[int(0.9 * n)] > ELLIPSE_TOLERANCE[0] or strays[-1] > ELLIPSE_TOLERANCE[1]:
        return None
    turn = {int(math.degrees(math.atan2((y - cy) / ry, (x - cx) / rx)) % 360 // 10) for x, y in points}
    if len(turn) < ELLIPSE_TURN * 36:
        return None
    if abs(rx - ry) <= CIRCLE_ROUNDNESS * max(rx, ry):
        rx = ry = (rx + ry) / 2
    return Ellipse(strokes[0].color, mean_pressure(strokes), (cx, cy), (rx, ry), list(strokes))


# Arrows

def arrow(shaft_stroke: Stroke, head_strokes: list[Stroke]) -> Optional[Arrow]:
    shaft = [p[:2] for p in shaft_stroke.points]
    length = path_length(shaft)
    if length < ARROW_MIN_MM * MM:
        return None
    tail, tip = shaft[0], shaft[-1]
    control = curve_through(shaft)
    curve = polyline_points(quadratic(tail, control, tip, 50), 100)
    if any(nearest(curve, p) > SHAFT_TOLERANCE * length for p in shaft[::3]):
        return None
    head = head_of([[p[:2] for p in s.points] for s in head_strokes])
    if head is None:
        return None
    apex, ends = head
    if math.dist(apex, tail) < math.dist(apex, tip):
        tail, tip = tip, tail
    if math.dist(apex, tip) > TIP_TOLERANCE * length:
        return None
    back = (control[0] - tip[0], control[1] - tip[1])
    sides = [(e[0] - apex[0], e[1] - apex[1]) for e in ends]
    if cross(back, sides[0]) * cross(back, sides[1]) >= 0:
        return None  # both sides of the head on the same side of the shaft
    for side in sides:
        if not (HEAD_ANGLES[0] <= angle_between(back, side) <= HEAD_ANGLES[1]
                and HEAD_LENGTHS[0] * length <= math.hypot(*side) <= HEAD_LENGTHS[1] * length):
            return None
    tail, control = straighten(tail, control, tip)
    strokes = [shaft_stroke] + list(head_strokes)
    return Arrow(shaft_stroke.color, mean_pressure(strokes), tail, control, tip, strokes)


def curve_through(points):
    """Control point of the quadratic curve from the first point to the last, through the middle one."""
    (ax, ay), (bx, by) = points[0], points[-1]
    mx, my = point_at(points, path_length(points) / 2)
    return 2 * mx - (ax + bx) / 2, 2 * my - (ay + by) / 2


def head_of(strokes):
    """The head's tip and the far ends of its two sides: one V stroke, or two strokes meeting at the tip."""
    if len(strokes) == 1:
        s = strokes[0]
        a, b = s[0], s[-1]
        return max(s, key=lambda p: distance_to_line(p, a, b)), (a, b)
    s, t = strokes
    gap, near_s, near_t, far_s, far_t = min(
        (math.dist(p, q), p, q, pf, qf)
        for p, pf in ((s[0], s[-1]), (s[-1], s[0])) for q, qf in ((t[0], t[-1]), (t[-1], t[0])))
    if gap > HEAD_GAP_MM * MM:
        return None
    return ((near_s[0] + near_t[0]) / 2, (near_s[1] + near_t[1]) / 2), (far_s, far_t)


def straighten(tail, control, tip):
    """A shaft that hardly bends becomes straight, and a straight one snaps to multiples of 45°."""
    length = math.dist(tail, tip)
    middle = ((tail[0] + tip[0]) / 2, (tail[1] + tip[1]) / 2)
    if math.dist(control, middle) > STRAIGHT_BEND * length:
        return tail, control
    direction = math.degrees(math.atan2(tail[1] - tip[1], tail[0] - tip[0]))
    snapped = round(direction / 45) * 45
    if abs(direction - snapped) <= SNAP_DEGREES:
        a = math.radians(snapped)
        tail = (tip[0] + length * math.cos(a), tip[1] + length * math.sin(a))
    return tail, ((tail[0] + tip[0]) / 2, (tail[1] + tip[1]) / 2)


# The sketchy look

HEAD_ANGLE = 28
# Sketched lines get thinner over this length at both ends, so the round ends of lines
# meeting at a corner make no blob, down to TAPER_MIN of their width.
TAPER_MM = 3
TAPER_MIN = 0.3
# Sketched lines are drawn with segments this long.
SEGMENT_MM = 0.5
HEAD_SIZE = (0.2, 3, 10)  # relative to the shaft, between these many mm


def sketch(shape: Shape) -> list[list[tuple[float, float]]]:
    """The shape as hand-drawn-looking polylines in pad units, the same each time it is drawn."""
    if isinstance(shape, Box):
        rng = random.Random(seed(shape.rect))
        x0, y0, x1, y1 = shape.rect
        corners = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
        return [line for a, b in zip(corners, corners[1:] + corners[:1]) for line in rough_line(a, b, rng)]
    if isinstance(shape, Ellipse):
        return rough_ellipse(shape.center, shape.radii, random.Random(seed(shape.center + shape.radii)))
    rng = random.Random(seed(shape.tail + shape.tip))
    lines = rough_curve(shape.tail, shape.control, shape.tip, rng)
    back = (shape.control[0] - shape.tip[0], shape.control[1] - shape.tip[1])
    shaft = path_length(quadratic(shape.tail, shape.control, shape.tip, 20))
    size = min(max(HEAD_SIZE[0] * shaft, HEAD_SIZE[1] * MM), HEAD_SIZE[2] * MM)
    for turn in (HEAD_ANGLE, -HEAD_ANGLE):
        a = math.atan2(back[1], back[0]) + math.radians(turn)
        end = (shape.tip[0] + size * math.cos(a), shape.tip[1] + size * math.sin(a))
        lines += rough_line(shape.tip, end, rng)
    return lines


def taper(line):
    """Width factor of each segment of a sketched line."""
    total = path_length(line)
    factors, walked = [], 0
    for a, b in zip(line, line[1:]):
        middle = walked + math.dist(a, b) / 2
        walked += math.dist(a, b)
        end = min(middle, total - middle)
        factors.append(min(1, TAPER_MIN + (1 - TAPER_MIN) * end / (TAPER_MM * MM)))
    return factors


def seed(numbers):
    return hash(tuple(round(n) for n in numbers))


def rough_line(a, b, rng):
    """Two passes over a line, each slightly off, bowed, and running a little past its ends."""
    length = math.dist(a, b)
    if length == 0:
        return [[a, b]]
    ux, uy = (b[0] - a[0]) / length, (b[1] - a[1]) / length
    lines = []
    for _ in range(2):
        jitter = min(0.6 * MM, 0.02 * length)
        start_over, end_over = rng.uniform(-0.3, 1.2) * MM, rng.uniform(-0.3, 1.2) * MM
        s = (a[0] - ux * start_over - uy * rng.uniform(-jitter, jitter),
             a[1] - uy * start_over + ux * rng.uniform(-jitter, jitter))
        e = (b[0] + ux * end_over - uy * rng.uniform(-jitter, jitter),
             b[1] + uy * end_over + ux * rng.uniform(-jitter, jitter))
        bow = rng.uniform(-1, 1) * min(0.012 * length, 1.5 * MM)
        control = ((s[0] + e[0]) / 2 - uy * bow * 2, (s[1] + e[1]) / 2 + ux * bow * 2)
        lines.append(quadratic(s, control, e, max(4, int(length / (SEGMENT_MM * MM)))))
    return lines


def rough_ellipse(center, radii, rng):
    """Two passes round the ellipse, each slightly off and wavy, starting anywhere and overlapping a little."""
    (cx, cy), (rx, ry) = center, radii
    perimeter = math.pi * (rx + ry)
    lines = []
    for _ in range(2):
        start, overlap = rng.uniform(0, 2 * math.pi), math.radians(rng.uniform(10, 25))
        wave, phase = rng.uniform(0.01, 0.025), rng.uniform(0, 2 * math.pi)
        shift = (rng.uniform(-0.01, 0.01) * rx, rng.uniform(-0.01, 0.01) * ry)
        n = max(24, int(perimeter / (SEGMENT_MM * MM)))
        line = []
        for k in range(n + 1):
            t = start + (2 * math.pi + overlap) * k / n
            r = 1 + wave * math.sin(2 * t + phase)
            line.append((cx + shift[0] + rx * r * math.cos(t), cy + shift[1] + ry * r * math.sin(t)))
        lines.append(line)
    return lines


def rough_curve(a, control, b, rng):
    length = path_length(quadratic(a, control, b, 20))
    jitter = min(1 * MM, 0.02 * length)

    def shift(p):
        return p[0] + rng.uniform(-jitter, jitter), p[1] + rng.uniform(-jitter, jitter)
    return [quadratic(shift(a), shift(control), shift(b), max(6, int(length / (SEGMENT_MM * MM)))) for _ in range(2)]


# Geometry

def mean_pressure(strokes):
    pressures = [p[2] for s in strokes for p in s.points]
    return sum(pressures) / len(pressures)


def path_length(points):
    return sum(math.dist(a[:2], b[:2]) for a, b in zip(points, points[1:]))


def resample(points, step):
    """Points at least step apart along the path, so dense and sparse drawing weigh the same."""
    kept = [points[0][:2]]
    for p in points[1:]:
        if math.dist(p[:2], kept[-1]) >= step:
            kept.append(p[:2])
    return kept


def point_at(points, distance):
    walked = 0
    for a, b in zip(points, points[1:]):
        step = math.dist(a, b)
        if step and walked + step >= distance:
            t = (distance - walked) / step
            return a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t
        walked += step
    return points[-1]


def polyline_points(points, n):
    """n points spread evenly along a polyline."""
    total = path_length(points)
    return [point_at(points, total * k / n) for k in range(n + 1)]


def quadratic(a, control, b, n):
    return [((1 - t) ** 2 * a[0] + 2 * (1 - t) * t * control[0] + t * t * b[0],
             (1 - t) ** 2 * a[1] + 2 * (1 - t) * t * control[1] + t * t * b[1])
            for t in (k / n for k in range(n + 1))]


def nearest(points, p):
    return min(math.dist(p, q) for q in points)


def distance_to_line(p, a, b):
    length = math.dist(a, b)
    if length == 0:
        return math.dist(p, a)
    return abs((p[0] - a[0]) * (b[1] - a[1]) - (p[1] - a[1]) * (b[0] - a[0])) / length


def cross(u, v):
    return u[0] * v[1] - u[1] * v[0]


def angle_between(u, v):
    norms = math.hypot(*u) * math.hypot(*v)
    if norms == 0:
        return 180
    return math.degrees(math.acos(max(-1, min(1, (u[0] * v[0] + u[1] * v[1]) / norms))))
