import datetime as dt

from .base import BaseType


class Datetime(BaseType[dt.datetime]):
    @classmethod
    def deserialize(cls, value: int) -> dt.datetime:
        return dt.datetime.fromtimestamp(value, tz=dt.UTC)

    @classmethod
    def serialize(cls, value: dt.datetime) -> int:
        return int(value.timestamp())


class Timestamp(Datetime):
    @classmethod
    def deserialize(cls, value: int) -> dt.datetime:
        return dt.datetime.fromtimestamp(value / 1e6, tz=dt.UTC)

    @classmethod
    def serialize(cls, value: dt.datetime) -> int:
        return int(value.timestamp() * 1e6)
