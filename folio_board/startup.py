"""Startup: build the driven adapters, the hexagon, then the driver adapters, and run them."""
import signal
import sys

import gi

gi.require_version('Gtk', '4.0')
gi.require_version('GLibUnix', '2.0')
from gi.repository import GLib, GLibUnix, Gtk  # noqa: E402

from folio_board.adapter.for_encoding_images.cairo import CairoEncoder  # noqa: E402
from folio_board.adapter.for_presenting_drawings.gtk import BoardWindow  # noqa: E402
from folio_board.adapter.for_receiving_pen_input.tuhi.live import TuhiError, TuhiPad  # noqa: E402
from folio_board.adapter.for_sharing_drawings.gtk_clipboard import GtkClipboard  # noqa: E402
from folio_board.adapter.for_storing_drawings.filesystem import FileSystemStorage  # noqa: E402
from folio_board.adapter.for_telling_time.monotonic import MonotonicClock  # noqa: E402
from folio_board.hexagon.application import FolioBoard  # noqa: E402


def main(argv):
    try:
        pad = TuhiPad(argv[1] if len(argv) > 1 else None)
    except TuhiError as e:
        sys.exit(str(e))
    board = FolioBoard(pad.dimensions_um(), pad=pad, encoder=CairoEncoder(),
                       storage=FileSystemStorage(), sharing=GtkClipboard(), clock=MonotonicClock())

    app = Gtk.Application(application_id='io.github.FolioBoard')

    def on_activate(app):
        win = BoardWindow(app, board)
        board.set_presenter(win)
        win.connect('close-request', lambda *_: board.stop() or False)
        win.present()
        pad.drive(board)
        board.start()

    app.connect('activate', on_activate)
    for signum in (signal.SIGINT, signal.SIGTERM):
        GLibUnix.signal_add_full(GLib.PRIORITY_DEFAULT, signum, lambda: app.quit() or GLib.SOURCE_REMOVE)
    try:
        app.run([])
    finally:
        pad.close()
