import decimal

from .base import BaseType


class Float(float, BaseType[float]):
    pass


class Decimal(decimal.Decimal, BaseType[decimal.Decimal]):
    pass
