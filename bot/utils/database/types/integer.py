from .base import BaseType


class Int32(int, BaseType[int]):
    pass


class Int64(int, BaseType[int]):
    pass


class Uint8(int, BaseType[int]):
    pass


class Uint16(int, BaseType[int]):
    pass


class Uint64(int, BaseType[int]):
    pass
