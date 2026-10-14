"""The presenter frames the area to save or copy."""


def frame(app, start, end):
    app.begin_crop(start)
    app.drag_crop(end)
    app.end_crop(is_click=False, min_size=10)


def click(app, at):
    app.begin_crop(at)
    app.drag_crop(at)
    app.end_crop(is_click=True, min_size=10)


def test_dragging_frames_an_area_whichever_way(world):
    frame(world.app, (5000, 6000), (1000, 2000))
    assert world.app.page().crop == (1000, 2000, 5000, 6000)
    assert world.presenter.redraws == 2


def test_frame_stays_on_the_page(world):
    frame(world.app, (-500, 20000), (3000, 99999))
    assert world.app.page().crop == (0, 20000, 3000, 21000)


def test_click_inside_keeps_the_crop(world):
    frame(world.app, (1000, 1000), (5000, 5000))
    click(world.app, (3000, 3000))
    assert world.app.page().crop == (1000, 1000, 5000, 5000)


def test_click_outside_drops_the_crop(world):
    frame(world.app, (1000, 1000), (5000, 5000))
    click(world.app, (8000, 3000))
    assert world.app.page().crop is None


def test_click_off_the_page_drops_the_crop(world):
    frame(world.app, (1000, 1000), (5000, 5000))
    click(world.app, (-300, 3000))
    assert world.app.page().crop is None


def test_click_without_a_crop_leaves_none(world):
    click(world.app, (3000, 3000))
    assert world.app.page().crop is None


def test_dragging_along_an_edge_frames_nothing(world):
    frame(world.app, (-100, 1000), (-50, 9000))
    assert world.app.page().crop is None


def test_new_drag_replaces_the_crop(world):
    frame(world.app, (1000, 1000), (5000, 5000))
    frame(world.app, (2000, 2000), (3000, 3000))
    assert world.app.page().crop == (2000, 2000, 3000, 3000)


def test_rotating_drops_the_crop(world):
    frame(world.app, (1000, 1000), (5000, 5000))
    world.app.rotate()
    assert world.app.page().crop is None
