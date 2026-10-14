"""Draw a Page with cairo: used both for the screen and for image files."""
import cairo

# Never draw thinner than this in output pixels, so light strokes stay visible.
MIN_OUTPUT_WIDTH = 1.0


def draw_page(cr, page, scale):
    """Draw the white page and its strokes; cr is already scaled to page units, by scale."""
    cr.rectangle(0, 0, page.width, page.height)
    cr.set_source_rgb(1, 1, 1)
    cr.fill()

    cr.set_line_cap(cairo.LINE_CAP_ROUND)
    cr.set_line_join(cairo.LINE_JOIN_ROUND)
    cr.set_source_rgb(0.08, 0.08, 0.1)
    floor = MIN_OUTPUT_WIDTH / scale
    for x0, y0, x1, y1, width in page.segments:
        cr.set_line_width(max(floor, width))
        cr.move_to(x0, y0)
        cr.line_to(x1, y1)
        cr.stroke()
