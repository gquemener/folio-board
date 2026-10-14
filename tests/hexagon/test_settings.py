"""The orientation and pressure settings are kept between sessions, and clearing keeps them."""
from folio_board.hexagon.driver.for_presenting_drawings import Settings


def test_settings_start_as_portrait_with_pressure(world):
    world.app.start()
    assert world.app.settings() == Settings('portrait', True)
    assert world.presenter.settings_shown == 1


def test_start_brings_back_the_kept_settings_and_shows_them(world):
    world.settings_memory.settings = Settings('landscape', False)
    world.app.start()
    assert world.app.settings() == Settings('landscape', False)
    assert world.app.view_size() == (21000, 14800)
    assert world.presenter.settings_shown == 1
    assert world.settings_memory.remembered == 0


def test_settings_that_cannot_be_restored_stay_default_and_say_why(world):
    world.settings_memory.error = 'bad file'
    world.app.start()
    assert world.app.settings() == Settings()
    assert world.presenter.toasts == ['Could not restore the settings: bad file']
    assert world.presenter.settings_shown == 1


def test_changing_a_setting_keeps_it(world):
    world.app.set_orientation('landscape')
    assert world.settings_memory.settings == Settings('landscape', True)
    world.app.set_pressure_sensitive(False)
    assert world.settings_memory.settings == Settings('landscape', False)


def test_setting_what_is_already_set_does_nothing(world):
    world.app.set_orientation('portrait')
    world.app.set_pressure_sensitive(True)
    assert world.settings_memory.remembered == 0
    assert world.presenter.redraws == 0


def test_clearing_keeps_the_settings(world):
    world.app.set_orientation('landscape')
    world.app.set_pressure_sensitive(False)
    world.app.clear()
    assert world.app.settings() == Settings('landscape', False)
    assert world.settings_memory.settings == Settings('landscape', False)


def test_settings_that_cannot_be_kept_still_apply_and_say_why(world):
    world.settings_memory.error = 'disk full'
    world.app.set_orientation('landscape')
    assert world.app.view_size() == (21000, 14800)
    assert world.presenter.statuses == ['Could not keep the settings: disk full']
