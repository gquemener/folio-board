"""Hand-drawn boxes, circles and arrows become clean, sketchy ones; the rest stays as drawn.

The samples were drawn on a Bamboo Folio, area by area, on a guide page: see SAMPLE_AREAS.
"""
import json
import math
import pathlib

import pytest

from folio_board.hexagon.driven.for_remembering_the_drawing import Arrow, Box, Ellipse, Stroke
from tests.hexagon.conftest import A5_UM

SAMPLES = json.loads((pathlib.Path(__file__).parent.parent / 'fixtures' / 'shape_samples.json').read_text())['items']
# Indexes in SAMPLES of the strokes drawn in each area of the guide page.
SAMPLE_AREAS = {
    'box in 4 strokes': [1, 2, 3, 4],  # stroke 0 is the pen touching the paper by accident
    'small box in 4 strokes': [5, 6, 7, 8],
    'box in 2 strokes': [9, 10],
    'box in 3 strokes': [11, 12, 13],
    'flat box in 1 stroke': [14],
    'box in 1 stroke': [15],
    'other box in 1 stroke': [16],
    'curved arrow with a head in 2 strokes': [17, 18, 19],
    'arrow to the right': [20, 21],
    'arrow to the left': [22, 23],
    'arrow up': [24, 25],
    'arrow down and right': [26, 27],
    'circle': [46],
}
HANDWRITING = list(range(28, 43))  # "Login OK Cancel"
DOODLES = [43, 44, 45, 47]  # U, L, line, tilted box
PAUSE = 0.4


def replay(world, indexes, pause=PAUSE, color_between=None):
    for n, i in enumerate(indexes):
        if color_between is not None and n:
            world.app.set_color(color_between)
        stroke = SAMPLES[i]
        for x, y, p in stroke['points']:
            world.app.pen(True, x, y, max(1, round(p * 2047)))
            world.clock.advance(0.004)
        world.app.pen(True, x, y, 0)
        world.clock.advance(pause)


def draw(world, points, pressure=0.4):
    for x, y in points:
        world.app.pen(True, round(x), round(y), round(pressure * 2047))
        world.clock.advance(0.004)
    world.app.pen(True, round(x), round(y), 0)
    world.clock.advance(PAUSE)


def ellipse_points(rx, ry, turn=1.1, center=(15000, 10000)):
    """A hand-drawn-like ellipse, slightly wavy, going round turn times, radii in mm."""
    return [(center[0] + rx * 100 * (1 + 0.03 * math.sin(3 * t)) * math.cos(t),
             center[1] + ry * 100 * (1 + 0.03 * math.sin(3 * t)) * math.sin(t))
            for t in (2 * math.pi * turn * k / 400 for k in range(401))]


def shapes(world):
    return [item for item in world.memory.items if not isinstance(item, Stroke)]


@pytest.fixture
def world(world):
    world.app.pad_resized(297000, 216000)  # the samples were drawn on an A4 Folio
    return world


@pytest.mark.parametrize('area', SAMPLE_AREAS)
def test_each_sample_snaps_to_its_shape(world, area):
    replay(world, SAMPLE_AREAS[area])
    kind = Box if 'box' in area else Ellipse if area == 'circle' else Arrow
    assert [type(s) for s in shapes(world)] == [kind]
    # The shape keeps the strokes as drawn.
    assert [[p[:2] for p in s.points] for s in shapes(world)[0].strokes] == [
        [tuple(p[:2]) for p in SAMPLES[i]['points']] for i in SAMPLE_AREAS[area]]


def test_the_whole_page_snaps_boxes_and_arrows_only(world):
    replay(world, range(len(SAMPLES)))
    assert [type(s).__name__ for s in shapes(world)] == ['Box'] * 7 + ['Arrow'] * 5 + ['Ellipse']
    snapped = sum(len(v) for v in SAMPLE_AREAS.values())
    assert len(world.memory.items) == len(SAMPLES) - snapped + 13


@pytest.mark.parametrize('indexes', [HANDWRITING, DOODLES], ids=['handwriting', 'doodles'])
def test_handwriting_and_doodles_stay_as_drawn(world, indexes):
    replay(world, indexes)
    assert shapes(world) == []


def test_a_box_takes_the_place_of_its_strokes(world):
    replay(world, [0, 1, 2, 3, 4])
    dot, box = world.memory.items
    assert isinstance(dot, Stroke) and isinstance(box, Box)
    x0, y0, x1, y1 = box.rect
    assert (x1 - x0, y1 - y0) == pytest.approx((3350, 4180), abs=100)  # about 33 x 42 mm
    assert box.color == 0
    assert 0 < box.pressure < 1


def test_a_nearly_round_ellipse_becomes_a_circle(world):
    replay(world, SAMPLE_AREAS['circle'])  # drawn about 17 x 20 mm
    circle = shapes(world)[0]
    assert circle.radii[0] == circle.radii[1] == pytest.approx(913, abs=50)


def test_a_wide_ellipse_stays_an_ellipse(world):
    draw(world, ellipse_points(30, 12))
    (rx, ry), = [s.radii for s in shapes(world)]
    assert (rx, ry) == pytest.approx((3000, 1200), rel=0.05)


@pytest.mark.parametrize('turn', [0.5, 0.75])
def test_an_arc_stays_as_drawn(world, turn):
    draw(world, ellipse_points(15, 15, turn))
    assert shapes(world) == []


def test_a_small_circle_stays_as_drawn(world):
    draw(world, ellipse_points(3.5, 3.5))  # 7 mm across, like a letter
    assert shapes(world) == []


def test_a_pause_between_strokes_splits_the_box(world):
    replay(world, SAMPLE_AREAS['box in 4 strokes'], pause=2)
    assert shapes(world) == []


def test_changing_color_between_strokes_splits_the_box(world):
    replay(world, SAMPLE_AREAS['box in 2 strokes'], color_between=4)
    assert shapes(world) == []


def test_a_shape_keeps_its_strokes_color(world):
    world.app.set_color(4)
    replay(world, SAMPLE_AREAS['box in 1 stroke'])
    assert shapes(world)[0].color == 4


def test_clearing_forgets_the_strokes_drawn_before(world):
    replay(world, [9])
    world.app.clear()
    replay(world, [10])
    assert shapes(world) == []


def test_without_shapes_everything_stays_as_drawn(world):
    world.app.set_shapes(False)
    replay(world, SAMPLE_AREAS['box in 1 stroke'] + SAMPLE_AREAS['arrow up'])
    assert shapes(world) == []
    world.app.set_shapes(True)
    replay(world, SAMPLE_AREAS['box in 1 stroke'])
    assert len(shapes(world)) == 1


def test_a_curved_arrow_keeps_its_curve(world):
    replay(world, SAMPLE_AREAS['curved arrow with a head in 2 strokes'])
    arrow = shapes(world)[0]
    middle = ((arrow.tail[0] + arrow.tip[0]) / 2, (arrow.tail[1] + arrow.tip[1]) / 2)
    assert abs(arrow.control[0] - middle[0]) + abs(arrow.control[1] - middle[1]) > 500


def test_an_arrow_points_where_its_head_is(world):
    replay(world, SAMPLE_AREAS['arrow up'])  # the shaft was drawn from the bottom up
    arrow = shapes(world)[0]
    tail, tip = world.app.board.to_view(*arrow.tail), world.app.board.to_view(*arrow.tip)
    assert tip[1] < tail[1]


def test_a_nearly_upright_arrow_is_made_upright(world):
    replay(world, SAMPLE_AREAS['arrow up'])
    arrow = shapes(world)[0]
    assert arrow.tail[1] == pytest.approx(arrow.tip[1])  # pad y is across the page in portrait
    assert arrow.control == pytest.approx(((arrow.tail[0] + arrow.tip[0]) / 2, arrow.tip[1]))


def test_a_shape_looks_the_same_each_time_it_is_drawn(world):
    replay(world, SAMPLE_AREAS['box in 1 stroke'])
    assert world.app.page().segments == world.app.page().segments
    world.app.start()  # brought back from memory
    assert world.app.page().segments == world.app.page().segments


def test_shape_width_follows_the_pressure_setting(world):
    replay(world, SAMPLE_AREAS['box in 1 stroke'])
    box = shapes(world)[0]
    widths = [s[4] for s in world.app.page().segments]
    assert max(widths) == pytest.approx(20 + 220 * box.pressure)
    world.app.set_pressure_sensitive(False)
    assert max(s[4] for s in world.app.page().segments) == pytest.approx(80)
    assert min(s[4] for s in world.app.page().segments) < 80  # thinner at the ends


def test_the_shapes_setting_is_kept(world):
    world.app.set_shapes(False)
    assert world.settings_memory.settings.shapes is False


def test_a5_pad_sizes_do_not_matter(world):
    world.app.pad_resized(*A5_UM)
    replay(world, SAMPLE_AREAS['box in 1 stroke'])
    assert len(shapes(world)) == 1
