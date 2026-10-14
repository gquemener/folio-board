import pytest

from folio_board.adapter.for_remembering_the_drawing.json_file import JsonFileMemory, default_path
from folio_board.hexagon.driven.for_remembering_the_drawing import RememberingError, Stroke


def test_recalls_what_it_remembered_last(tmp_path):
    path = str(tmp_path / 'state' / 'drawing.json')
    JsonFileMemory(path).remember([Stroke(1, [(1, 2, 0.5)])])
    JsonFileMemory(path).remember([Stroke(3, [(10, 20, 0.123456), (11, 21, 1.0)]), Stroke(0, [])])
    assert JsonFileMemory(path).recall() == [Stroke(3, [(10, 20, 0.1235), (11, 21, 1.0)]), Stroke(0, [])]


def test_nothing_remembered_is_an_empty_drawing(tmp_path):
    assert JsonFileMemory(str(tmp_path / 'drawing.json')).recall() == []


def test_unreadable_file_is_a_remembering_error(tmp_path):
    path = tmp_path / 'drawing.json'
    path.write_text('{"strokes": [{"colour": 1}]}')
    with pytest.raises(RememberingError):
        JsonFileMemory(str(path)).recall()


def test_failure_to_write_is_a_remembering_error(tmp_path):
    (tmp_path / 'file').write_text('')
    with pytest.raises(RememberingError):
        JsonFileMemory(str(tmp_path / 'file' / 'drawing.json')).remember([])


def test_lives_in_the_state_directory(monkeypatch):
    monkeypatch.setenv('XDG_STATE_HOME', '/state')
    assert default_path() == '/state/folio-board/drawing.json'
