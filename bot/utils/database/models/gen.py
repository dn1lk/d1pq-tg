import json
from typing import Annotated, ClassVar

import ydb

import misc
from utils.database import types
from utils.database.base import Column

from .base import WithDates, WithToken

DEFAULT_STICKER_SET = "TextAnimated"


class GenSettings(WithDates, WithToken):
    __tablename__: ClassVar[str] = "gen_settings"

    __slots__ = (
        "accuracy",
        "chance",
        "chat_id",
        "created_at",
        "token",
        "updated_at",
        "with_messages",
        "with_stickers",
    )

    chat_id: Annotated[int, Column(types.Int64, is_primary_key=True)]
    chance: Annotated[float, Column(types.Percent, default=0.1)]
    accuracy: Annotated[int, Column(types.Uint8, default=2)]
    with_messages: Annotated[bool, Column(types.Bool, default=True)]
    with_stickers: Annotated[bool, Column(types.Bool, default=True)]

    @property
    def messages(self) -> list[str]:
        assert self.with_messages is True, "messages disabled"

        filename = self._get_filename(f"{self.chat_id}:messages")
        encryptor = self._encryptor

        messages = self._read_file(misc.MNT_PATH / "messages" / filename, encryptor)
        messages = json.loads(messages) if messages else []

        return messages

    @messages.setter
    def messages(self, messages: list[str]) -> None:
        assert self.with_messages is True, "messages disabled"

        filename = self._get_filename(f"{self.chat_id}:messages")
        encryptor = self._encryptor

        self._write_file(misc.MNT_PATH / "messages" / filename, encryptor, json.dumps(messages))

    @messages.deleter
    def messages(self) -> None:
        assert self.with_messages is False, "messages enabled"

        filename = self._get_filename(f"{self.chat_id}:messages")
        self._remove_file(misc.MNT_PATH / "messages" / filename)

    @property
    def stickers(self) -> list[str]:
        assert self.with_stickers is True, "stickers disabled"

        filename = self._get_filename(f"{self.chat_id}:stickers")
        encryptor = self._encryptor

        stickers = self._read_file(misc.MNT_PATH / "stickers" / filename, encryptor)
        stickers = json.loads(stickers) if stickers else []

        return stickers

    @stickers.setter
    def stickers(self, stickers: list[str]) -> None:
        assert self.with_stickers is True, "stickers disabled"

        filename = self._get_filename(f"{self.chat_id}:stickers")
        encryptor = self._encryptor

        self._write_file(misc.MNT_PATH / "stickers" / filename, encryptor, json.dumps(stickers))

    @stickers.deleter
    def stickers(self) -> None:
        assert self.with_stickers is False, "stickers enabled"

        filename = self._get_filename(f"{self.chat_id}:stickers")
        self._remove_file(misc.MNT_PATH / "stickers" / filename)

    @classmethod
    async def setup(cls) -> None:
        (misc.MNT_PATH / "messages").mkdir(parents=True, exist_ok=True)
        (misc.MNT_PATH / "stickers").mkdir(parents=True, exist_ok=True)

        return await super().setup()

    async def delete(self) -> ydb.convert.ResultSets | None:
        self.with_messages = False
        del self.messages

        self.with_stickers = False
        del self.stickers

        return await super().delete()
