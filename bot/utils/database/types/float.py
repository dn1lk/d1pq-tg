import decimal
from typing import Self

from .base import BaseType


class Float(float, BaseType[float]):
    pass


class Decimal(decimal.Decimal, BaseType[decimal.Decimal]):
    pass


class Percent(float, BaseType[float]):
    @classmethod
    def __queryname__(cls) -> str:
        return "Uint8"

    @classmethod
    def deserialize(cls, value: int) -> Self:
        return cls(value / 100)

    def serialize(self) -> int:
        return int(self * 100)
