"""ForEncodingImages with cairo: SVG sized in points, true to paper, or 200 DPI PNG."""
import io

import cairo

from folio_board.hexagon.driven.for_encoding_images import EncodingError, ForEncodingImages
from folio_board.hexagon.driver.for_presenting_drawings import UNIT_MM
from folio_board.lib.cairo_page import draw_page

PNG_DPI = 200
MM_PER_INCH = 25.4


class CairoEncoder(ForEncodingImages):
    def encode(self, page, fmt):
        x0, y0, x1, y1 = page.crop or (0, 0, page.width, page.height)
        w, h = x1 - x0, y1 - y0
        out = io.BytesIO()
        try:
            if fmt == 'svg':
                scale = UNIT_MM * 72 / MM_PER_INCH
                surface = cairo.SVGSurface(out, w * scale, h * scale)
            else:
                scale = UNIT_MM * PNG_DPI / MM_PER_INCH
                surface = cairo.ImageSurface(cairo.FORMAT_RGB24, max(1, round(w * scale)), max(1, round(h * scale)))
            cr = cairo.Context(surface)
            cr.scale(scale, scale)
            cr.translate(-x0, -y0)
            draw_page(cr, page, scale)
            if isinstance(surface, cairo.ImageSurface):
                surface.write_to_png(out)
            surface.finish()
        except cairo.Error as e:
            raise EncodingError(str(e)) from e
        return out.getvalue()
