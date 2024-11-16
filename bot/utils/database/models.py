import datetime as dt
from typing import Annotated, ClassVar

import ydb

from . import types
from .base import Column, Index, Model

DEFAULT_STICKER_SET = "TextAnimated"


def _datetime_now():
    return types.Timestamp.now(tz=dt.UTC)


class WithDates(Model):
    updated: Annotated[types.Timestamp, Column(types.Timestamp, on_update=_datetime_now, default=_datetime_now)]
    created: Annotated[types.Timestamp, Column(types.Timestamp, default=_datetime_now)]


class MainSettings(WithDates):
    __tablename__: ClassVar[str] = "main_settings"

    chat_id: Annotated[types.Int64, Column(types.Int64, is_primary_key=True)]
    locale: Annotated[types.Utf8, Column(types.Utf8)]
    members: Annotated[types.JsonList[int] | None, Column(types.JsonList, is_null=True)]
    commands: Annotated[types.JsonDict[str, str] | None, Column(types.JsonDict, is_null=True)]


class GenSettings(WithDates):
    __tablename__: ClassVar[str] = "gen_settings"

    chat_id: Annotated[types.Int64, Column(types.Int64, is_primary_key=True)]
    chance: Annotated[types.Float, Column(types.Float, default=types.Float(0.1))]
    accuracy: Annotated[types.Uint8, Column(types.Uint8, default=types.Uint8(2))]
    messages: Annotated[types.JsonList[str] | None, Column(types.JsonList, is_null=True)]
    stickers: Annotated[types.JsonList[str] | None, Column(types.JsonList, is_null=True)]


class GPTSettings(WithDates):
    __tablename__: ClassVar[str] = "gpt_settings"

    chat_id: Annotated[types.Int64, Column(types.Int64, is_primary_key=True)]
    temperature: Annotated[types.Float, Column(types.Float, default=types.Float(0.6))]
    max_tokens: Annotated[types.Uint16, Column(types.Uint16, default=types.Uint16(100))]
    tokens: Annotated[types.Int16, Column(types.Int16, default=types.Int16(5000))]
    promt: Annotated[types.Utf8, Column(types.Utf8)]

    async def delete(self) -> ydb.convert.ResultSets:
        self.temperature = types.Float(0.6)
        self.max_tokens = types.Uint16(100)

        return await self.save()


class Transactions(WithDates):
    __tablename__: ClassVar[str] = "transactions"
    __indices__: ClassVar[list[Index]] = [Index("user_chat_ids", ["user_id", "chat_id"], ["amount"])]

    id: Annotated[types.Uint64, Column(types.Uint64, is_primary_key=True)]
    user_id: Annotated[types.Int64, Column(types.Int64)]
    chat_id: Annotated[types.Int64, Column(types.Int64)]
    amount: Annotated[types.Decimal, Column(types.Decimal)]
