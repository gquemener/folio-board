"""Pen input becomes strokes on the page, turned to the page's orientation."""
import pytest

from folio_board.hexagon.application import FALLBACK_DIMENSIONS_UM, FolioBoard
from tests.doubles import FakeClock, FakePad, InMemoryMemory, InMemoryStorage, SharingSpy, StubEncoder


def draw(app, *points, pressure=1024):
    for x, y in points:
        app.pen(True, x, y, pressure)
    app.pen(True, *points[-1], 0)


def test_page_is_the_pad_turned_to_portrait(world):
    assert world.app.view_size() == (14800, 21000)
    page = world.app.page()
    assert (page.width, page.height, page.segments, page.crop, page.hover) == (14800, 21000, (), None, None)
    assert len(page.palette) == 16


def test_unknown_pad_size_falls_back_to_a4():
    app = FolioBoard((0, 0), FakePad(), StubEncoder(), InMemoryStorage(), SharingSpy(), FakeClock(),
                     InMemoryMemory())
    assert app.view_size() == (FALLBACK_DIMENSIONS_UM[1] // 10, FALLBACK_DIMENSIONS_UM[0] // 10)


def test_pad_resize_changes_page_and_ignores_empty_sizes(world):
    world.app.pad_resized(0, 0)
    assert world.app.view_size() == (14800, 21000)
    world.app.pad_resized(297000, 216000)
    assert world.app.view_size() == (21600, 29700)


def test_pen_down_draws_a_stroke_and_redraws(world):
    draw(world.app, (3100, 200), (3300, 400))
    segments = world.app.page().segments
    # Portrait shows pad (x, y) at (width - y, x); the first point is a dot.
    assert [s[:4] for s in segments] == [(14600, 3100, 14600, 3100), (14600, 3100, 14400, 3300)]
    assert world.presenter.redraws == 3


def test_lifting_the_pen_starts_a_new_stroke(world):
    draw(world.app, (3100, 100), (3200, 200))
    draw(world.app, (3500, 500))
    assert len(world.app.page().segments) == 3
    world.app.clear()
    assert world.app.page().segments == ()


def test_hover_follows_the_pen_until_it_leaves(world):
    world.app.pen(True, 3100, 200, 0)
    assert world.app.page().hover == (14600, 3100)
    assert world.app.page().segments == ()
    world.app.pen(False, 0, 0, 0)
    assert world.app.page().hover is None


@pytest.mark.parametrize('pressure_max, pressure, width', [
    (2047, 0, None),      # lifted: nothing drawn
    (2047, 2047, 240),    # hardest: 2.4 mm
    (2047, 4000, 240),    # beyond the maximum is the maximum
    (None, 2047, 240),    # unknown maximum falls back to the Folio's
    (1023, 1023, 240),    # the maximum the pad reports
])
def test_pressure_sets_line_width(world, pressure_max, pressure, width):
    world.app.pad_connected(pressure_max)
    world.app.pen(True, 3010, 10, pressure)
    segments = world.app.page().segments
    assert (segments[0][4] if segments else None) == pytest.approx(width)


def test_light_pressure_draws_thin_lines(world):
    world.app.pad_connected(2000)
    world.app.pen(True, 3010, 10, 1)
    assert world.app.page().segments[0][4] == pytest.approx(20 + 220 / 2000)


def test_without_pressure_sensitivity_every_line_is_0_8_mm(world):
    world.app.set_pressure_sensitive(False)
    draw(world.app, (3010, 10), (3020, 20), pressure=2047)
    assert [s[4] for s in world.app.page().segments] == pytest.approx([80, 80])


def test_segments_average_the_pressure_of_their_ends(world):
    world.app.pad_connected(2000)
    world.app.pen(True, 3010, 10, 1)
    world.app.pen(True, 3020, 20, 2000)
    assert world.app.page().segments[1][4] == pytest.approx(20 + 220 * (1 / 2000 + 1) / 2)


@pytest.mark.parametrize('turns, size, point', [
    (0, (14800, 21000), (14600, 3100)),   # portrait
    (1, (21000, 14800), (3100, 200)),     # landscape
    (2, (14800, 21000), (200, 17900)),    # reverse portrait
    (3, (21000, 14800), (17900, 14600)),  # reverse landscape
    (4, (14800, 21000), (14600, 3100)),   # full turn
])
def test_rotating_turns_the_page(world, turns, size, point):
    world.app.pen(True, 3100, 200, 1000)
    for _ in range(turns):
        world.app.rotate()
    page = world.app.page()
    assert (page.width, page.height) == size
    assert page.segments[0][:2] == point
