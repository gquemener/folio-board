import pytest

from folio_board.adapter.for_storing_drawings.filesystem import FileSystemStorage
from folio_board.hexagon.driven.for_storing_drawings import StorageError


def test_stores_and_replaces(tmp_path):
    path = tmp_path / 'a.svg'
    FileSystemStorage().store(str(path), b'one')
    FileSystemStorage().store(str(path), b'two')
    assert path.read_bytes() == b'two'


def test_failure_is_a_storage_error(tmp_path):
    with pytest.raises(StorageError, match='No such file'):
        FileSystemStorage().store(str(tmp_path / 'missing' / 'a.svg'), b'x')
