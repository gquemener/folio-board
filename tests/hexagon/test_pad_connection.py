"""The application waits for the pad, and waits again when it does not show up or drops."""
from folio_board.hexagon.application import RETRY_SECONDS


def test_start_waits_for_the_pad(world):
    world.app.start()
    assert world.pad.calls == ['stop_live', 'start_live']
    assert world.presenter.connected is False
    assert world.presenter.toasts == []


def test_connected_pad_can_be_reconnected(world):
    world.app.start()
    world.app.pad_connected(2047)
    assert world.presenter.connected is True
    world.app.reconnect()
    assert world.pad.calls[-2:] == ['stop_live', 'start_live']
    assert world.presenter.connected is False


def test_failing_start_is_reported(world):
    world.pad.fail_with = 3
    world.app.start()
    assert world.presenter.toasts == ['Could not reach the pad (3)']
    assert world.presenter.connected is False


def test_waits_again_when_the_pad_does_not_show_up(world):
    world.app.start()
    world.clock.advance(RETRY_SECONDS - 1)
    world.app.check_connection()
    assert world.pad.calls.count('start_live') == 1
    world.clock.advance(1)
    world.app.check_connection()
    assert world.pad.calls.count('start_live') == 2


def test_connected_pad_is_left_alone(world):
    world.app.start()
    world.app.pad_connected(2047)
    world.clock.advance(RETRY_SECONDS * 3)
    world.app.check_connection()
    assert world.pad.calls.count('start_live') == 1


def test_lost_pad_is_waited_for_again(world):
    world.app.start()
    world.app.pad_connected(2047)
    world.app.pad_lost(5)
    assert world.presenter.toasts == ['Pad link lost (5), retrying…']
    assert world.presenter.connected is False
    world.clock.advance(RETRY_SECONDS)
    world.app.check_connection()
    assert world.pad.calls.count('start_live') == 2


def test_stopping_on_request_is_not_a_loss(world):
    world.app.start()
    world.app.pad_connected(2047)
    world.app.pad_lost(0)
    assert world.presenter.connected is True
    assert world.presenter.toasts == []


def test_stop_stops_the_pad(world):
    world.app.stop()
    assert world.pad.calls == ['stop_live']
