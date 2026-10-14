"""The palette strip along the pad's top edge: tapping a box picks the color of the next strokes."""
import pytest

from folio_board.hexagon import palette

# The A5 test pad is 14800 units wide in portrait: 16 boxes of 925 units, 1500 units (15 mm) high.
BOX = 925


def tap(app, portrait_x, portrait_y=700):
    """Tap the pen at a point given as seen in portrait: pad x is portrait y, pad y is 14800 - portrait x."""
    app.pen(True, portrait_y, 14800 - portrait_x, 800)
    app.pen(True, portrait_y, 14800 - portrait_x, 0)


def stroke(app, *pad_points):
    for x, y in pad_points:
        app.pen(True, x, y, 1000)
    app.pen(True, *pad_points[-1], 0)


def colors(app):
    return [s[5] for s in app.page().segments]


def test_black_is_picked_at_first(world):
    stroke(world.app, (5000, 5000), (6000, 6000))
    assert set(colors(world.app)) == {(0, 0, 0)}
    assert [s.selected for s in world.app.page().palette] == [True] + [False] * 15


@pytest.mark.parametrize('index', range(16))
def test_tapping_a_box_picks_its_color(world, index):
    tap(world.app, index * BOX + BOX / 2)
    stroke(world.app, (5000, 5000), (6000, 6000))
    name, value = palette.COLORS[index]
    assert set(colors(world.app)) == {palette.rgb(value)}
    assert world.presenter.toasts == [name]
    assert [s.selected for s in world.app.page().palette].index(True) == index


def test_tapping_draws_nothing(world):
    tap(world.app, 3 * BOX)
    assert world.app.page().segments == ()


def test_sliding_off_the_strip_draws_nothing_until_the_pen_lifts(world):
    world.app.pen(True, 700, 5000, 800)
    world.app.pen(True, 4000, 5000, 800)
    world.app.pen(True, 6000, 5000, 800)
    assert world.app.page().segments == ()
    world.app.pen(True, 6000, 5000, 0)
    stroke(world.app, (7000, 5000))
    assert len(world.app.page().segments) == 1


def test_leaving_range_ends_the_tap(world):
    world.app.pen(True, 700, 5000, 800)
    world.app.pen(False, 0, 0, 0)
    stroke(world.app, (7000, 5000))
    assert len(world.app.page().segments) == 1


def test_strokes_keep_their_color(world):
    tap(world.app, 4 * BOX + 10)                # red
    stroke(world.app, (5000, 5000))
    tap(world.app, 1 * BOX + 10)                # blue
    stroke(world.app, (8000, 8000))
    assert colors(world.app) == [palette.rgb(0xAA0000), palette.rgb(0x0000AA)]
    world.app.undo()
    assert colors(world.app) == [palette.rgb(0xAA0000)]


def test_a_stroke_may_run_into_the_strip(world):
    stroke(world.app, (2000, 5000), (500, 5000), (300, 7000))
    assert len(world.app.page().segments) == 3
    assert world.presenter.toasts == []


def test_the_strip_is_15_mm_high(world):
    world.app.pen(True, 1499, 5000, 800)    # 14.99 mm from the top edge: on the strip
    world.app.pen(True, 1499, 5000, 0)
    world.app.pen(True, 1500, 5000, 800)    # 15 mm: on the page
    world.app.pen(True, 1500, 5000, 0)
    assert len(world.app.page().segments) == 1
    assert len(world.presenter.toasts) == 1


def test_boxes_cover_the_whole_width(world):
    tap(world.app, 0)
    tap(world.app, 14800)
    assert world.presenter.toasts == ['Black', 'White']


def test_swatches_lie_along_the_top_in_portrait(world):
    swatches = world.app.page().palette
    assert [s.name for s in swatches] == [name for name, _ in palette.COLORS]
    assert swatches[0].rect == (0, 0, BOX, 1500)
    assert swatches[15].rect == (15 * BOX, 0, 14800, 1500)


@pytest.mark.parametrize('turns, first, last', [
    # A quarter turn: black, top left in portrait, goes to the bottom of the left edge.
    (1, (0, 14800 - BOX, 1500, 14800), (0, 0, 1500, BOX)),
    (2, (14800 - BOX, 21000 - 1500, 14800, 21000), (0, 21000 - 1500, BOX, 21000)),  # upside down: bottom
    (3, (21000 - 1500, 0, 21000, BOX), (21000 - 1500, 14800 - BOX, 21000, 14800)),  # right edge
])
def test_the_strip_stays_on_the_pads_top_edge_when_rotating(world, turns, first, last):
    for _ in range(turns):
        world.app.rotate()
    swatches = world.app.page().palette
    assert (swatches[0].rect, swatches[15].rect) == (first, last)


def test_picking_survives_clearing(world):
    tap(world.app, 2 * BOX + 10)
    world.app.clear()
    stroke(world.app, (5000, 5000))
    assert colors(world.app) == [palette.rgb(0x00AA00)]
