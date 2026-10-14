"""The drawing is kept between sessions, until the presenter clears it."""
from folio_board.hexagon.driven.for_remembering_the_drawing import Stroke


def draw(app, *points, pressure=1024):
    for x, y in points:
        app.pen(True, x, y, pressure)
    app.pen(True, *points[-1], 0)


def test_start_brings_back_the_kept_drawing(world):
    world.memory.items = [Stroke(4, [(3100, 200, 0.5), (3300, 400, 0.5)])]
    world.app.start()
    segments = world.app.page().segments
    assert [s[:4] for s in segments] == [(14600, 3100, 14600, 3100), (14600, 3100, 14400, 3300)]
    assert segments[0][5] == (2 / 3, 0, 0)  # red
    assert world.presenter.redraws == 1


def test_start_with_nothing_kept_shows_an_empty_page(world):
    world.app.start()
    assert world.app.page().segments == ()


def test_a_drawing_that_cannot_be_restored_leaves_the_page_empty_and_says_why(world):
    world.memory.error = 'bad file'
    world.app.start()
    assert world.app.page().segments == ()
    assert world.presenter.toasts == ['Could not restore the last drawing: bad file']
    assert world.pad.calls[-1] == 'start_live'


def test_each_stroke_is_kept_when_the_pen_lifts(world):
    world.app.pen(True, 3100, 200, 1000)
    world.app.pen(True, 3200, 300, 1000)
    assert world.memory.remembered == 0  # not while drawing
    world.app.pen(True, 3200, 300, 0)
    assert world.memory.items == [Stroke(0, [(3100, 200, 1000 / 2047), (3200, 300, 1000 / 2047)])]
    world.app.pen(False, 0, 0, 0)
    assert world.memory.remembered == 1


def test_picking_a_color_keeps_nothing(world):
    world.app.pen(True, 2000, 7000, 1000)
    world.app.pen(True, 2000, 7000, 0)
    assert world.memory.remembered == 0


def test_clear_is_kept(world):
    draw(world.app, (3100, 200))
    world.app.clear()
    assert world.memory.items == []


def test_stopping_keeps_a_stroke_still_under_way(world):
    world.app.pen(True, 3100, 200, 1000)
    world.app.stop()
    assert len(world.memory.items) == 1


def test_a_drawing_that_cannot_be_kept_says_why_and_stays_on_the_page(world):
    world.memory.error = 'disk full'
    draw(world.app, (3100, 200))
    assert world.presenter.statuses == ['Could not keep the drawing: disk full']
    assert len(world.app.page().segments) == 1
