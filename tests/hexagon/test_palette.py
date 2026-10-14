"""The presenter picks the pen color with the keys & é " ' ( - è _ ç of a French keyboard: black,
orange, blue, green, yellow, red, lilac, pink and brown. The whole pad is for drawing."""
import pytest

from folio_board.hexagon import palette
from folio_board.hexagon.driver.for_presenting_drawings import PenColor

NAMES = ['Black', 'Orange', 'Blue', 'Green', 'Yellow', 'Red', 'Lilac', 'Pink', 'Brown']


def stroke(app, *pad_points):
    for x, y in pad_points:
        app.pen(True, x, y, 1000)
    app.pen(True, *pad_points[-1], 0)


def colors(app):
    return [s[5] for s in app.page().segments]


def test_the_palette_has_nine_colors_in_key_order():
    assert [name for name, _ in palette.COLORS] == NAMES


def test_black_is_picked_at_first(world):
    stroke(world.app, (5000, 5000), (6000, 6000))
    assert set(colors(world.app)) == {(0, 0, 0)}
    assert world.app.page().pen.name == 'Black'


@pytest.mark.parametrize('index', range(9))
def test_picking_a_color_draws_the_next_strokes_in_it_and_says_so(world, index):
    world.app.set_color(index)
    stroke(world.app, (5000, 5000), (6000, 6000))
    name, value = palette.COLORS[index]
    assert set(colors(world.app)) == {palette.rgb(value)}
    assert world.presenter.toasts == [name]
    assert world.app.page().pen == PenColor(name, palette.rgb(value))


@pytest.mark.parametrize('index', [-1, 9, 15])
def test_other_colors_are_left_alone(world, index):
    world.app.set_color(2)
    world.app.set_color(index)
    assert world.app.page().pen.name == 'Blue'
    assert world.presenter.toasts == ['Blue']


def test_strokes_keep_their_color(world):
    world.app.set_color(5)
    stroke(world.app, (5000, 5000))
    world.app.set_color(2)
    stroke(world.app, (8000, 8000))
    assert colors(world.app) == [palette.rgb(0xD62828), palette.rgb(0x1E5BD6)]


def test_the_top_of_the_pad_is_for_drawing(world):
    stroke(world.app, (0, 7000), (2200, 7000))
    assert len(world.app.page().segments) == 2
    assert world.presenter.toasts == []


def test_the_color_survives_clearing(world):
    world.app.set_color(3)
    world.app.clear()
    stroke(world.app, (5000, 5000))
    assert colors(world.app) == [palette.rgb(0x2E9D46)]
