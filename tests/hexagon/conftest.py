from types import SimpleNamespace

import pytest

from folio_board.hexagon.application import FolioBoard
from tests.doubles import FakeClock, FakePad, InMemoryStorage, PresenterSpy, SharingSpy, StubEncoder

# A5 pad: 21000 x 14800 units, so 14800 x 21000 when shown in portrait.
A5_UM = (210000, 148000)


@pytest.fixture
def world():
    """The hexagon wired to test doubles; the test drives it through its two driver ports."""
    w = SimpleNamespace(pad=FakePad(), encoder=StubEncoder(), storage=InMemoryStorage(),
                        sharing=SharingSpy(), presenter=PresenterSpy(), clock=FakeClock())
    w.app = FolioBoard(A5_UM, w.pad, w.encoder, w.storage, w.sharing, w.clock)
    w.app.set_presenter(w.presenter)
    return w
