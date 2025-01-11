import datetime as dt
from typing import Self

from .base import BaseType


class Datetime(dt.datetime, BaseType[int]):
    @classmethod
    def deserialize(cls, value: int) -> Self:
        return cls.fromtimestamp(value, tz=dt.UTC)

    def serialize(self) -> int:
        return int(self.timestamp())

    @classmethod
    def now(cls, tz: dt.tzinfo | None = dt.UTC) -> Self:
        return super().now(tz=tz)
