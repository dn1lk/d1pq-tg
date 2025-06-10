from typing import Annotated, ClassVar

import ydb

from utils.database import types
from utils.database.base import Column

from .base import WithDates


class GPTSettings(WithDates):
    __tablename__: ClassVar[str] = "gpt_settings"

    __slots__ = (
        "chat_id",
        "created_at",
        "max_tokens",
        "promt",
        "temperature",
        "token",
        "tokens",
        "updated_at",
    )

    chat_id: Annotated[int, Column(types.Int64, is_primary_key=True)]
    temperature: Annotated[float, Column(types.Percent, default=0.6)]
    max_tokens: Annotated[int, Column(types.Int32, default=100)]
    tokens: Annotated[int, Column(types.Int32, default=5000)]
    promt: Annotated[str | None, Column(types.Utf8, is_null=True)]

    async def delete(self) -> ydb.convert.ResultSets | None:
        self.temperature = 0.6
        self.max_tokens = 100

        return await self.save()
