"""FolioBoard: the application, as its driver actors (presenter and pad) see it."""
import os

from folio_board.hexagon import palette
from folio_board.hexagon.board import FALLBACK_PRESSURE_MAX, Board
from folio_board.hexagon.driven.for_encoding_images import EncodingError, ForEncodingImages
from folio_board.hexagon.driven.for_linking_the_pad import ForLinkingThePad, PadLinkError
from folio_board.hexagon.driven.for_notifying_the_presenter import ForNotifyingThePresenter
from folio_board.hexagon.driven.for_remembering_the_drawing import ForRememberingTheDrawing, RememberingError
from folio_board.hexagon.driven.for_sharing_drawings import ForSharingDrawings
from folio_board.hexagon.driven.for_storing_drawings import ForStoringDrawings, StorageError
from folio_board.hexagon.driven.for_telling_time import ForTellingTime
from folio_board.hexagon.driver.for_presenting_drawings import UNIT_UM, ForPresentingDrawings, Page
from folio_board.hexagon.driver.for_receiving_pen_input import ForReceivingPenInput

# The pad link tries to reach the pad for ~25 s per start, then gives up: start again after this.
RETRY_SECONDS = 30
# A4 Bamboo Folio / Slate size, used until the pad reports the real one.
FALLBACK_DIMENSIONS_UM = (297000, 216000)


class _NoPresenter(ForNotifyingThePresenter):
    """Stands in until the presenter's screen exists."""

    def page_changed(self):
        pass

    def status(self, text):
        pass

    def toast(self, text):
        pass

    def reconnect_available(self, available):
        pass


class FolioBoard(ForPresentingDrawings, ForReceivingPenInput):

    def __init__(self, pad_size_um, pad: ForLinkingThePad, encoder: ForEncodingImages,
                 storage: ForStoringDrawings, sharing: ForSharingDrawings, clock: ForTellingTime,
                 memory: ForRememberingTheDrawing):
        w_um, h_um = pad_size_um
        if not w_um or not h_um:
            w_um, h_um = FALLBACK_DIMENSIONS_UM
        self.board = Board(w_um // UNIT_UM, h_um // UNIT_UM)
        self.pad, self.encoder, self.storage, self.sharing, self.clock = pad, encoder, storage, sharing, clock
        self.memory = memory
        self.presenter: ForNotifyingThePresenter = _NoPresenter()
        self.connected = False
        self.started_at = 0

    def set_presenter(self, presenter: ForNotifyingThePresenter):
        """The presenter's screen is made after the application, since it drives it too."""
        self.presenter = presenter

    # ForPresentingDrawings

    def start(self):
        try:
            self.board.strokes = self.memory.recall()
        except RememberingError as e:
            self.presenter.toast(f'Could not restore the last drawing: {e}')
        self.presenter.page_changed()
        self._start_live()

    def stop(self):
        self.pad.stop_live()
        self._remember()  # a stroke may still be under way

    def reconnect(self):
        self._start_live()

    def clear(self):
        self.board.clear()
        self._remember()
        self.presenter.page_changed()

    def set_orientation(self, orientation):
        self.board.set_orientation(orientation)
        self.presenter.page_changed()

    def set_pressure_sensitive(self, on):
        self.board.pressure_sensitive = on
        self.presenter.page_changed()

    def begin_crop(self, at):
        self.board.begin_crop(at)

    def drag_crop(self, at):
        self.board.drag_crop(at)
        self.presenter.page_changed()

    def end_crop(self, is_click, min_size):
        self.board.end_crop(is_click, min_size)
        self.presenter.page_changed()

    def save(self, path):
        fmt = 'svg' if path.lower().endswith('.svg') else 'png'
        try:
            self.storage.store(path, self.encoder.encode(self.page(), fmt))
        except (EncodingError, StorageError) as e:
            self.presenter.status(f'Save failed: {e}')
            return
        self.presenter.status(f'Saved {os.path.basename(path)}')

    def copy(self):
        page = self.page()
        try:
            svg, png = self.encoder.encode(page, 'svg'), self.encoder.encode(page, 'png')
        except EncodingError as e:
            self.presenter.status(f'Copy failed: {e}')
            return
        self.sharing.share(svg, png)
        self.presenter.toast('Copied')

    def view_size(self):
        return self.board.view_size

    def page(self):
        vw, vh = self.board.view_size
        hover = self.board.to_view(*self.board.hover) if self.board.hover else None
        return Page(vw, vh, self.board.segments(), self.board.crop, hover, self.board.swatches())

    # ForReceivingPenInput

    def pen(self, in_range, x, y, pressure):
        drawing = self.board.current
        if self.board.pen(in_range, x, y, pressure):
            self.presenter.toast(palette.COLORS[self.board.color][0])
        if drawing is not None and self.board.current is not drawing:
            self._remember()  # the pen lifted: the stroke is done
        self.presenter.page_changed()

    def pad_connected(self, pressure_max):
        self.board.pressure_max = pressure_max or FALLBACK_PRESSURE_MAX
        self._set_connected(True)
        self.presenter.status('Connected, draw away')

    def pad_lost(self, code):
        if code != 0:
            self._set_connected(False)
            self.presenter.status(f'Live mode stopped ({code}), retrying…')

    def pad_resized(self, width_um, height_um):
        if width_um and height_um:
            self.board.pad_w, self.board.pad_h = width_um // UNIT_UM, height_um // UNIT_UM
            self.presenter.page_changed()

    def check_connection(self):
        if not self.connected and self.clock.now() - self.started_at >= RETRY_SECONDS:
            self._start_live()

    def _remember(self):
        try:
            self.memory.remember(self.board.strokes)
        except RememberingError as e:
            self.presenter.status(f'Could not keep the drawing: {e}')

    def _start_live(self):
        self.pad.stop_live()
        self._set_connected(False)
        self.started_at = self.clock.now()
        try:
            self.pad.start_live()
        except PadLinkError as e:
            self.presenter.status(f'StartLive failed ({e.code})')
            return
        self.presenter.status('Waiting for the Folio… press its button')

    def _set_connected(self, connected):
        self.connected = connected
        # Restarting while a connection attempt is pending makes the pad link fail it,
        # so reconnecting is only offered once a connection has been made.
        self.presenter.reconnect_available(connected)
