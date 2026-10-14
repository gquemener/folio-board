import io
import re

import pytest

cairo = pytest.importorskip('cairo')

from folio_board.adapter.for_encoding_images.cairo import CairoEncoder  # noqa: E402
from folio_board.hexagon.driver.for_presenting_drawings import Page  # noqa: E402

A4_PORTRAIT = Page(21600, 29700, ((1000, 1000, 5000, 8000, 50),), hover=(300, 300))
CROPPED = Page(21600, 29700, ((1000, 1000, 5000, 8000, 50),), crop=(1000, 1000, 8000, 5000))


def png_size(data):
    surface = cairo.ImageSurface.create_from_png(io.BytesIO(data))
    return surface.get_width(), surface.get_height()


def svg_size(data):
    head = data[:400].decode()
    return tuple(float(re.search(fr'{a}="([\d.]+)"', head).group(1)) for a in ('width', 'height'))


def test_png_is_200_dpi():
    assert png_size(CairoEncoder().encode(A4_PORTRAIT, 'png')) == (1701, 2339)


def test_png_keeps_only_the_crop():
    # 70 x 40 mm at 200 DPI.
    assert png_size(CairoEncoder().encode(CROPPED, 'png')) == (551, 315)


def test_svg_is_true_to_paper_size():
    width, height = svg_size(CairoEncoder().encode(CROPPED, 'svg'))
    assert (width, height) == (pytest.approx(70 / 25.4 * 72), pytest.approx(40 / 25.4 * 72))


def test_png_draws_the_stroke():
    data = CairoEncoder().encode(Page(1000, 1000, ((0, 500, 1000, 500, 100),)), 'png')
    surface = cairo.ImageSurface.create_from_png(io.BytesIO(data))
    stride, pixels = surface.get_stride(), surface.get_data()
    def pixel(x, y):
        return bytes(pixels[y * stride + 4 * x:y * stride + 4 * x + 3])
    w = surface.get_width()
    assert pixel(w // 2, w // 2) != b'\xff\xff\xff'
    assert pixel(w // 2, 2) == b'\xff\xff\xff'
