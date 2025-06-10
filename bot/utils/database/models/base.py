import datetime as dt
from functools import cached_property
from hashlib import sha256
from pathlib import Path
from typing import Annotated

from cryptography.fernet import Fernet

from utils.database import types
from utils.database.base import Column, Model


class WithDates(Model):
    updated_at: Annotated[dt.datetime, Column(types.Timestamp, default=dt.datetime.now, on_update=dt.datetime.now)]
    created_at: Annotated[dt.datetime, Column(types.Timestamp, default=dt.datetime.now)]


class WithToken(Model):
    token: Annotated[str, Column(types.Utf8, default=lambda: Fernet.generate_key().decode())]

    def _get_filename(self, destiny: str, extension: str = "txt") -> str:
        filename = sha256(f"{self.token}:{destiny}".encode()).hexdigest()
        return f"{filename}.{extension}"

    @cached_property
    def _encryptor(self) -> Fernet:
        encryptor = Fernet(self.token)
        return encryptor

    def _read_file(self, path: Path, encryptor: Fernet) -> bytes:
        if not path.exists():
            return b""

        text_bytes = path.read_bytes()
        text_bytes = encryptor.decrypt(text_bytes)
        return text_bytes

    def _write_file(self, path: Path, encryptor: Fernet, text: str) -> None:
        text_bytes = text.encode()
        text_bytes = encryptor.encrypt(text_bytes)
        path.write_bytes(text_bytes)

    def _remove_file(self, path: Path) -> None:
        path.unlink(missing_ok=True)
