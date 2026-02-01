import os

from storage.base import StorageBackend


class LocalStorage(StorageBackend):
    def __init__(self, root_dir: str):
        self.root_dir = root_dir
        os.makedirs(self.root_dir, exist_ok=True)

    def put(self, key: str, data: bytes) -> str:
        path = os.path.join(self.root_dir, key)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "wb") as handle:
            handle.write(data)
        return key

    def get(self, key: str) -> bytes:
        path = os.path.join(self.root_dir, key)
        with open(path, "rb") as handle:
            return handle.read()
