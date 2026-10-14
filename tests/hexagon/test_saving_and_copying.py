"""The presenter saves the page, or the framed area, to a file or the clipboard."""


def test_save_picks_the_format_from_the_extension(world):
    world.app.save('/pics/sketch.SVG')
    world.app.save('/pics/sketch.png')
    world.app.save('/pics/sketch')
    assert world.storage.files == {'/pics/sketch.SVG': b'svg image', '/pics/sketch.png': b'png image',
                                   '/pics/sketch': b'png image'}
    assert world.presenter.toasts[-1] == 'Saved sketch'


def test_save_encodes_the_page_with_its_crop(world):
    world.app.pen(True, 3100, 100, 500)
    world.app.begin_crop((0, 0))
    world.app.drag_crop((4000, 3000))
    world.app.end_crop(False, 10)
    world.app.save('a.svg')
    page, fmt = world.encoder.pages[0]
    assert (fmt, page.crop, len(page.segments)) == ('svg', (0, 0, 4000, 3000), 1)


def test_failed_save_says_why(world):
    world.storage.error = 'disk full'
    world.app.save('a.png')
    assert world.presenter.toasts == ['Save failed: disk full']
    world.storage.error, world.encoder.error = None, 'too big'
    world.app.save('a.png')
    assert world.presenter.toasts[-1] == 'Save failed: too big'
    assert world.storage.files == {}


def test_copy_shares_svg_and_png_and_says_so(world):
    world.app.copy()
    assert world.sharing.shared == [(b'svg image', b'png image')]
    assert world.presenter.toasts == ['Copied']


def test_failed_copy_says_why(world):
    world.encoder.error = 'too big'
    world.app.copy()
    assert world.sharing.shared == []
    assert world.presenter.toasts == ['Copy failed: too big']
