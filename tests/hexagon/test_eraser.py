"""With the eraser picked, every stroke or shape the pen touches goes away whole."""
from folio_board.hexagon.driven.for_remembering_the_drawing import Box, Stroke

# The eraser reaches 2.5 mm: 250 pad units.


def draw(app, *points, pressure=1000):
    for x, y in points:
        app.pen(True, x, y, pressure)
    app.pen(True, *points[-1], 0)


def strokes_at(world):
    return [item.points[0][:2] for item in world.app.board.items]


def test_picking_the_eraser_says_so_and_a_color_puts_it_away(world):
    world.app.pick_eraser()
    assert world.presenter.toasts == ['Eraser']
    assert world.app.page().eraser == 250
    world.app.set_color(2)
    assert world.app.page().eraser is None
    assert world.app.page().pen.name == 'Blue'


def test_touching_a_stroke_erases_it_whole(world):
    draw(world.app, (5000, 5000), (6000, 5000), (7000, 5000))
    draw(world.app, (5000, 9000), (7000, 9000))
    world.app.pick_eraser()
    draw(world.app, (6900, 5200))  # 2 mm from the end of the first stroke
    assert strokes_at(world) == [(5000, 9000)]


def test_the_eraser_draws_nothing(world):
    world.app.pick_eraser()
    draw(world.app, (5000, 5000), (6000, 6000))
    assert world.app.board.items == []
    assert world.app.page().segments == ()


def test_the_eraser_misses_what_is_out_of_its_reach(world):
    draw(world.app, (5000, 5000), (7000, 5000))
    world.app.pick_eraser()
    draw(world.app, (6000, 5300), (8000, 5300))  # 3 mm away, along it
    assert len(world.app.board.items) == 1


def test_hovering_erases_nothing(world):
    draw(world.app, (5000, 5000), (7000, 5000))
    world.app.pick_eraser()
    world.app.pen(True, 6000, 5000, 0)
    assert len(world.app.board.items) == 1


def test_a_quick_swipe_erases_what_it_crosses(world):
    draw(world.app, (6000, 3000), (6000, 7000))
    draw(world.app, (9000, 3000), (9000, 7000))
    world.app.pick_eraser()
    draw(world.app, (5000, 5000), (8000, 5000))  # two reports, either side of the first stroke
    assert strokes_at(world) == [(9000, 3000)]


def test_a_dot_can_be_erased(world):
    draw(world.app, (5000, 5000))
    world.app.pick_eraser()
    draw(world.app, (5100, 5100))
    assert world.app.board.items == []


def test_touching_a_shape_erases_it_whole(world):
    world.memory.items = [Box(0, 0.5, (4000, 4000, 8000, 8000), []), Stroke(0, [(10000, 10000, 0.5)])]
    world.app.start()
    world.app.pick_eraser()
    draw(world.app, (6000, 6000))  # inside the box, far from its sides
    assert len(world.app.board.items) == 2
    draw(world.app, (6000, 8100))  # on its side
    assert [type(item) for item in world.app.board.items] == [Stroke]


def test_what_is_erased_is_kept_once_the_eraser_lifts(world):
    draw(world.app, (5000, 5000), (7000, 5000))
    draw(world.app, (5000, 9000), (7000, 9000))
    world.app.pick_eraser()
    remembered = world.memory.remembered
    world.app.pen(True, 6000, 5000, 800)
    world.app.pen(True, 6000, 9000, 800)
    assert world.memory.remembered == remembered  # not while erasing
    world.app.pen(True, 6000, 9000, 0)
    assert world.memory.items == []
    assert world.memory.remembered == remembered + 1


def test_erasing_nothing_keeps_nothing(world):
    world.app.pick_eraser()
    draw(world.app, (5000, 5000))
    assert world.memory.remembered == 0


def test_erasing_between_strokes_makes_no_shape_of_what_is_left(world):
    # Two sides of a box, then the eraser, then the other two sides: no box, and no trouble.
    draw(world.app, (4000, 4000), (4000, 8000))
    draw(world.app, (4000, 8000), (8000, 8000))
    world.app.pick_eraser()
    draw(world.app, (4000, 6000))
    world.app.set_color(0)
    draw(world.app, (8000, 8000), (8000, 4000))
    draw(world.app, (8000, 4000), (4000, 4000))
    assert all(isinstance(item, Stroke) for item in world.app.board.items)
    assert len(world.app.board.items) == 3
