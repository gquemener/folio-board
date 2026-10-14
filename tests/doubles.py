"""Test doubles for the hexagon's driven ports. Each records what the application asked of it."""
import copy

from folio_board.hexagon.driven.for_encoding_images import EncodingError, ForEncodingImages
from folio_board.hexagon.driven.for_linking_the_pad import ForLinkingThePad, PadLinkError
from folio_board.hexagon.driven.for_notifying_the_presenter import ForNotifyingThePresenter
from folio_board.hexagon.driven.for_remembering_settings import ForRememberingSettings, SettingsError
from folio_board.hexagon.driven.for_remembering_the_drawing import ForRememberingTheDrawing, RememberingError
from folio_board.hexagon.driven.for_sharing_drawings import ForSharingDrawings
from folio_board.hexagon.driven.for_storing_drawings import ForStoringDrawings, StorageError
from folio_board.hexagon.driven.for_telling_time import ForTellingTime
from folio_board.hexagon.driver.for_presenting_drawings import Settings


class FakePad(ForLinkingThePad):
    """ForLinkingThePad: start_live fails with fail_with, if set."""

    def __init__(self):
        self.calls = []
        self.fail_with = None

    def start_live(self):
        self.calls.append('start_live')
        if self.fail_with is not None:
            raise PadLinkError(self.fail_with)

    def stop_live(self):
        self.calls.append('stop_live')


class StubEncoder(ForEncodingImages):
    """ForEncodingImages: returns a recognisable fake image and keeps the pages it got."""

    def __init__(self):
        self.pages = []
        self.error = None

    def encode(self, page, fmt):
        if self.error:
            raise EncodingError(self.error)
        self.pages.append((page, fmt))
        return f'{fmt} image'.encode()


class InMemoryStorage(ForStoringDrawings):
    """ForStoringDrawings."""

    def __init__(self):
        self.files = {}
        self.error = None

    def store(self, path, data):
        if self.error:
            raise StorageError(self.error)
        self.files[path] = data


class InMemoryMemory(ForRememberingTheDrawing):
    """ForRememberingTheDrawing: keeps a copy of the strokes and shapes, as a file would."""

    def __init__(self, items=()):
        self.items = [copy.deepcopy(i) for i in items]
        self.remembered = 0
        self.error = None

    def remember(self, items):
        if self.error:
            raise RememberingError(self.error)
        self.items = copy.deepcopy(items)
        self.remembered += 1

    def recall(self):
        if self.error:
            raise RememberingError(self.error)
        return copy.deepcopy(self.items)


class InMemorySettings(ForRememberingSettings):
    """ForRememberingSettings."""

    def __init__(self, settings=Settings()):
        self.settings = settings
        self.remembered = 0
        self.error = None

    def remember(self, settings):
        if self.error:
            raise SettingsError(self.error)
        self.settings = settings
        self.remembered += 1

    def recall(self):
        if self.error:
            raise SettingsError(self.error)
        return self.settings


class SharingSpy(ForSharingDrawings):
    """ForSharingDrawings."""

    def __init__(self):
        self.shared = []

    def share(self, svg, png):
        self.shared.append((svg, png))


class PresenterSpy(ForNotifyingThePresenter):
    """ForNotifyingThePresenter."""

    def __init__(self):
        self.toasts = []
        self.redraws = 0
        self.settings_shown = 0
        self.connected = None

    def page_changed(self):
        self.redraws += 1

    def settings_changed(self):
        self.settings_shown += 1

    def toast(self, text):
        self.toasts.append(text)

    def connection_changed(self, connected):
        self.connected = connected


class FakeClock(ForTellingTime):
    """ForTellingTime: time only moves when a test says so."""

    def __init__(self):
        self.time = 1000.0

    def now(self):
        return self.time

    def advance(self, seconds):
        self.time += seconds
