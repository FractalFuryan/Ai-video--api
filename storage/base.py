from abc import ABC, abstractmethod


class StorageBackend(ABC):
    @abstractmethod
    def put(self, key: str, data: bytes) -> str:
        """Store bytes. Return storage_key used."""
        raise NotImplementedError

    @abstractmethod
    def get(self, key: str) -> bytes:
        """Fetch bytes by storage_key."""
        raise NotImplementedError
