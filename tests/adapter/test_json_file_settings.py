import pytest

from folio_board.adapter.for_remembering_settings.json_file import JsonFileSettings, default_path
from folio_board.hexagon.driven.for_remembering_settings import SettingsError
from folio_board.hexagon.driver.for_presenting_drawings import Settings


def test_recalls_what_it_remembered_last(tmp_path):
    path = str(tmp_path / 'state' / 'settings.json')
    JsonFileSettings(path).remember(Settings('landscape', True))
    JsonFileSettings(path).remember(Settings('landscape', False, False))
    assert JsonFileSettings(path).recall() == Settings('landscape', False, False)


def test_nothing_remembered_gives_the_defaults(tmp_path):
    assert JsonFileSettings(str(tmp_path / 'settings.json')).recall() == Settings()


def test_a_missing_setting_keeps_its_default(tmp_path):
    path = tmp_path / 'settings.json'
    path.write_text('{"pressure_sensitive": false}')
    assert JsonFileSettings(str(path)).recall() == Settings('portrait', False, True)


@pytest.mark.parametrize('content', ['not json', '[]', '{"orientation": "upside-down"}',
                                     '{"pressure_sensitive": "yes"}', '{"shapes": 1}'])
def test_unreadable_file_is_a_settings_error(tmp_path, content):
    path = tmp_path / 'settings.json'
    path.write_text(content)
    with pytest.raises(SettingsError):
        JsonFileSettings(str(path)).recall()


def test_failure_to_write_is_a_settings_error(tmp_path):
    (tmp_path / 'file').write_text('')
    with pytest.raises(SettingsError):
        JsonFileSettings(str(tmp_path / 'file' / 'settings.json')).remember(Settings())


def test_lives_in_the_state_directory(monkeypatch):
    monkeypatch.setenv('XDG_STATE_HOME', '/state')
    assert default_path() == '/state/folio-board/settings.json'
