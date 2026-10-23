"""
Contains the :class:`base class <tinydb.storages.Storage>` for storages and
implementations.
"""
import io
import json
import os
import warnings
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
__all__ = ('Storage', 'JSONStorage', 'MemoryStorage')

def touch(path: str, create_dirs: bool):
    """
    Create a file if it doesn't exist yet.

    :param path: The file to create.
    :param create_dirs: Whether to create all missing parent directories.
    """
    pass

class Storage(ABC):
    """
    The abstract base class for all Storages.

    A Storage (de)serializes the current state of the database and stores it in
    some place (memory, file on disk, ...).
    """

    @abstractmethod
    def read(self) -> Optional[Dict[str, Dict[str, Any]]]:
        """
        Read the current state.

        Any kind of deserialization should go here.

        Return ``None`` here to indicate that the storage is empty.
        """
        pass

    @abstractmethod
    def write(self, data: Dict[str, Dict[str, Any]]) -> None:
        """
        Write the current state of the database to the storage.

        Any kind of serialization should go here.

        :param data: The current state of the database.
        """
        pass

    def close(self) -> None:
        """
        Optional: Close open file handles, etc.
        """
        pass

class JSONStorage(Storage):
    """
    Store the data in a JSON file.
    """

    def __init__(self, path: str, create_dirs=False, encoding=None, access_mode='r+', **kwargs):
        """
        Create a new instance.

        Also creates the storage file, if it doesn't exist and the access mode
        is appropriate for writing.

        Note: Using an access mode other than `r` or `r+` will probably lead to
        data loss or data corruption!

        :param path: Where to store the JSON data.
        :param access_mode: mode in which the file is opened (r, r+)
        :type access_mode: str
        """
        super().__init__()
        self._mode = access_mode
        self.kwargs = kwargs
        if access_mode not in ('r', 'rb', 'r+', 'rb+'):
            warnings.warn("Using an `access_mode` other than 'r', 'rb', 'r+' or 'rb+' can cause data loss or corruption")
        if any([character in self._mode for character in ('+', 'w', 'a')]):
            touch(path, create_dirs=create_dirs)
        self._handle = open(path, mode=self._mode, encoding=encoding)

class MemoryStorage(Storage):
    """
    Store the data as JSON in memory.
    """

    def __init__(self):
        """
        Create a new instance.
        """
        super().__init__()
        self.memory = None