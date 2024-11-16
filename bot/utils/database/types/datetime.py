import datetime as dt
from typing import Self

from .base import BaseType


class Timestamp(dt.datetime, BaseType[int]):
    @classmethod
    def deserialize(cls, value: int) -> Self:
        return cls.fromtimestamp(value / 1e6, tz=dt.UTC)

    def serialize(self) -> int:
        return int(self.timestamp() * 1e6)
