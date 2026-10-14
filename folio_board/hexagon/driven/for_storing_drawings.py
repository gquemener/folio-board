"""Driven port for keeping saved drawings."""


class StorageError(Exception):
    pass


class ForStoringDrawings:
    def store(self, path: str, data: bytes) -> None:
        """Write data at path, replacing what is there; raises StorageError."""
        raise NotImplementedError
