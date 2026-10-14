"""The presenter's window, with GTK 4.

BoardWindow plays both sides of the presenter actor: it drives ForPresentingDrawings
with buttons, keys and mouse drags, and implements the driven port
ForNotifyingThePresenter to show the page, the status line and short messages.
"""
import os
import time

import gi

gi.require_version('Gtk', '4.0')
gi.require_version('Gdk', '4.0')
from gi.repository import Gdk, Gio, GLib, Gtk  # noqa: E402

import cairo  # noqa: E402

from folio_board.hexagon.driven.for_notifying_the_presenter import ForNotifyingThePresenter  # noqa: E402
from folio_board.hexagon.driver.for_presenting_drawings import ForPresentingDrawings  # noqa: E402
from folio_board.lib.cairo_page import draw_paper, draw_strokes  # noqa: E402

# A crop drag shorter than this, in screen pixels, is a click: outside the crop it drops it.
MIN_CROP_PIXELS = 8
TOAST_MS = 1500
TOAST_CSS = '.toast { background: rgba(0, 0, 0, 0.75); color: white; border-radius: 99px; padding: 8px 20px; }'


def pictures_dir():
    path = GLib.get_user_special_dir(GLib.UserDirectory.DIRECTORY_PICTURES)
    return path or os.path.expanduser('~/Pictures')


class BoardWindow(Gtk.ApplicationWindow, ForNotifyingThePresenter):
    def __init__(self, app, board: ForPresentingDrawings):
        super().__init__(application=app, title='Folio board')
        self.board = board
        self.set_default_size(700, 950)

        self.area = Gtk.DrawingArea()
        self.area.set_draw_func(self.on_draw)
        # A short message over the page, e.g. after copying; it lets clicks through to the page.
        self.toast_label = Gtk.Label(css_classes=['toast'])
        self.toast_revealer = Gtk.Revealer(child=self.toast_label, can_target=False,
                                           transition_type=Gtk.RevealerTransitionType.CROSSFADE,
                                           halign=Gtk.Align.CENTER, valign=Gtk.Align.END, margin_bottom=32)
        self.toast_timeout = None
        css = Gtk.CssProvider()
        css.load_from_string(TOAST_CSS)
        Gtk.StyleContext.add_provider_for_display(self.get_display(), css,
                                                  Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
        overlay = Gtk.Overlay(child=self.area)
        overlay.add_overlay(self.toast_revealer)
        self.set_child(overlay)

        header = Gtk.HeaderBar()
        for label, handler in (('Clear', self.confirm_clear), ('Rotate', board.rotate),
                               ('Reconnect', board.reconnect)):
            button = Gtk.Button(label=label)
            button.connect('clicked', lambda _b, h=handler: h())
            header.pack_start(button)
        self.reconnect_button = button
        button.set_sensitive(False)
        save = Gtk.Button(label='Save')
        save.connect('clicked', lambda _b: self.save())
        header.pack_end(save)
        copy = Gtk.Button(label='Copy', tooltip_text='Copy as SVG, to paste in Figma or Inkscape')
        copy.connect('clicked', lambda _b: board.copy())
        header.pack_end(copy)
        # Pressure sensitivity starts on, in the application too.
        self.pressure = Gtk.CheckButton(label='Pressure', active=True,
                                        tooltip_text='Vary line width with pen pressure')
        self.pressure.connect('toggled', lambda b: board.set_pressure_sensitive(b.get_active()))
        header.pack_end(self.pressure)
        self.status_label = Gtk.Label(label='Starting…')
        header.pack_end(self.status_label)
        self.set_titlebar(header)

        drag = Gtk.GestureDrag(button=Gdk.BUTTON_PRIMARY)
        drag.connect('drag-begin', self.on_crop_begin)
        drag.connect('drag-update', self.on_crop_update)
        drag.connect('drag-end', self.on_crop_end)
        self.area.add_controller(drag)
        self.crop_start = None

        keys = Gtk.EventControllerKey()
        keys.connect('key-pressed', self.on_key)
        self.add_controller(keys)

    # ForNotifyingThePresenter

    def page_changed(self):
        self.area.queue_draw()

    def status(self, text):
        self.status_label.set_label(text)

    def toast(self, text):
        self.toast_label.set_label(text)
        self.toast_revealer.set_reveal_child(True)
        if self.toast_timeout:
            GLib.source_remove(self.toast_timeout)
        self.toast_timeout = GLib.timeout_add(TOAST_MS, self.hide_toast)

    def reconnect_available(self, available):
        self.reconnect_button.set_sensitive(available)

    # Driving ForPresentingDrawings

    def on_key(self, _ctrl, keyval, _code, state):
        ctrl = state & Gdk.ModifierType.CONTROL_MASK
        if keyval in (Gdk.KEY_q, Gdk.KEY_Escape):
            self.close()
        elif keyval == Gdk.KEY_c and ctrl:
            self.board.copy()
        elif keyval == Gdk.KEY_c:
            self.confirm_clear()
        elif keyval == Gdk.KEY_r:
            self.board.rotate()
        elif keyval == Gdk.KEY_p:
            self.pressure.set_active(not self.pressure.get_active())
        elif keyval == Gdk.KEY_s and ctrl:
            self.save()
        return True

    def on_crop_begin(self, _gesture, x, y):
        self.crop_start = (x, y)
        self.board.begin_crop(self.to_page(x, y))

    def on_crop_update(self, _gesture, dx, dy):
        sx, sy = self.crop_start
        self.board.drag_crop(self.to_page(sx + dx, sy + dy))

    def on_crop_end(self, _gesture, dx, dy):
        is_click = abs(dx) < MIN_CROP_PIXELS and abs(dy) < MIN_CROP_PIXELS
        self.board.end_crop(is_click, MIN_CROP_PIXELS / self.page_transform()[2])
        self.crop_start = None

    def confirm_clear(self):
        if not self.board.page().segments:
            return  # nothing to lose
        dialog = Gtk.AlertDialog(message='Clear the drawing?',
                                 detail='It is kept between sessions until you clear it. This cannot be undone.',
                                 buttons=['Cancel', 'Clear'], cancel_button=0, default_button=0)
        dialog.choose(self, None, self.on_clear_chosen)

    def on_clear_chosen(self, dialog, result):
        try:
            if dialog.choose_finish(result) == 1:
                self.board.clear()
        except GLib.Error:
            pass  # dismissed

    def save(self):
        filters = Gio.ListStore.new(Gtk.FileFilter)
        for name, pattern in (('PNG image', '*.png'), ('SVG image', '*.svg')):
            file_filter = Gtk.FileFilter(name=name)
            file_filter.add_pattern(pattern)
            filters.append(file_filter)
        dialog = Gtk.FileDialog(title='Save drawing', filters=filters,
                                initial_name=time.strftime('folio-board-%Y-%m-%d-%H%M%S.png'))
        folder = pictures_dir()
        if os.path.isdir(folder):
            dialog.set_initial_folder(Gio.File.new_for_path(folder))
        dialog.save(self, None, self.on_save_chosen)

    def on_save_chosen(self, dialog, result):
        try:
            path = dialog.save_finish(result).get_path()
        except GLib.Error:
            return  # dismissed
        self.board.save(path)

    # Showing the page

    def hide_toast(self):
        self.toast_revealer.set_reveal_child(False)
        self.toast_timeout = None
        return GLib.SOURCE_REMOVE

    def page_transform(self):
        """Offset and scale that fit the page, centred, in the drawing area."""
        width, height = self.area.get_width(), self.area.get_height()
        vw, vh = self.board.view_size()
        scale = min(width / vw, height / vh)
        return (width - vw * scale) / 2, (height - vh * scale) / 2, scale

    def to_page(self, x, y):
        """Widget coordinates to page units; the point may lie off the page."""
        ox, oy, scale = self.page_transform()
        return (x - ox) / scale, (y - oy) / scale

    def draw_palette(self, cr, page, scale):
        """The palette strip, under the strokes, with the selected color framed."""
        for swatch in page.palette:
            x0, y0, x1, y1 = swatch.rect
            cr.rectangle(x0, y0, x1 - x0, y1 - y0)
            cr.set_source_rgb(*swatch.color)
            cr.fill_preserve()
            cr.set_source_rgb(0.75, 0.75, 0.78)
            cr.set_line_width(1 / scale)
            cr.stroke()
        for swatch in page.palette:
            if swatch.selected:
                x0, y0, x1, y1 = swatch.rect
                inset = 2.5 / scale
                cr.rectangle(x0 + inset, y0 + inset, x1 - x0 - 2 * inset, y1 - y0 - 2 * inset)
                cr.set_source_rgb(0.15, 0.15, 0.18)
                cr.set_line_width(3 / scale)
                cr.stroke_preserve()
                cr.set_source_rgb(1, 1, 1)
                cr.set_line_width(1 / scale)
                cr.stroke()

    def on_draw(self, _area, cr, _width, _height):
        cr.set_source_rgb(0.18, 0.18, 0.2)
        cr.paint()

        page = self.board.page()
        ox, oy, scale = self.page_transform()
        cr.translate(ox, oy)
        cr.scale(scale, scale)
        draw_paper(cr, page)
        self.draw_palette(cr, page, scale)
        draw_strokes(cr, page, scale)

        if page.crop:
            # Shade what the save leaves out and outline what it keeps.
            x0, y0, x1, y1 = page.crop
            cr.set_fill_rule(cairo.FILL_RULE_EVEN_ODD)
            cr.rectangle(0, 0, page.width, page.height)
            cr.rectangle(x0, y0, x1 - x0, y1 - y0)
            cr.set_source_rgba(0, 0, 0, 0.25)
            cr.fill()
            cr.rectangle(x0, y0, x1 - x0, y1 - y0)
            cr.set_source_rgb(0.2, 0.45, 0.9)
            cr.set_line_width(1.5 / scale)
            cr.set_dash([6 / scale, 4 / scale])
            cr.stroke()
            cr.set_dash([])

        if page.hover:
            cr.set_source_rgba(0.9, 0.2, 0.2, 0.7)
            cr.arc(*page.hover, 6 / scale, 0, 6.2832)
            cr.fill()
