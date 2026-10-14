"""Driven port for keeping saved drawings."""
from typing import Protocol


class StorageError(Exception):
    pass


class ForStoringDrawings(Protocol):
    def store(self, path: str, data: bytes) -> None:
        """Write data at path, replacing what is there; raises StorageError."""
