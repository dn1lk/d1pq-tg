import decimal

from .base import BaseType


class Float(BaseType[float]):
    pass


class Decimal(BaseType[decimal.Decimal]):
    pass


class Percent(BaseType[float]):
    @classmethod
    def __queryname__(cls) -> str:
        return "Uint8"

    @classmethod
    def deserialize(cls, value: int) -> float:
        return value / 100

    @classmethod
    def serialize(cls, value: float) -> int:
        return int(value * 100)
