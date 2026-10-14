"""ForSharingDrawings through the desktop clipboard, with GTK."""
import gi

gi.require_version('Gdk', '4.0')
from gi.repository import Gdk, GLib  # noqa: E402

from folio_board.hexagon.driven.for_sharing_drawings import ForSharingDrawings  # noqa: E402


class GtkClipboard(ForSharingDrawings):
    def share(self, svg, png):
        svg = GLib.Bytes.new(svg)
        # Browsers only hand web apps such as Figma plain text, so the SVG markup goes there too.
        Gdk.Display.get_default().get_clipboard().set_content(Gdk.ContentProvider.new_union([
            Gdk.ContentProvider.new_for_bytes('image/svg+xml', svg),
            Gdk.ContentProvider.new_for_bytes('text/plain;charset=utf-8', svg),
            Gdk.ContentProvider.new_for_bytes('image/png', GLib.Bytes.new(png)),
        ]))
