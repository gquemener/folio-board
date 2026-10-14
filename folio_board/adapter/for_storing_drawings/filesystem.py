"""ForStoringDrawings on the local file system."""
from folio_board.hexagon.driven.for_storing_drawings import StorageError


class FileSystemStorage:
    def store(self, path, data):
        try:
            with open(path, 'wb') as out:
                out.write(data)
        except OSError as e:
            raise StorageError(str(e)) from e
