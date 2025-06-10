import json

from .base import BaseType


class JsonBase[T](BaseType[T]):
    @classmethod
    def __queryname__(cls) -> str:
        return "Json"

    @classmethod
    def deserialize(cls, value: str) -> T:
        return json.loads(value)

    @classmethod
    def serialize(cls, value: T) -> str:
        return json.dumps(value)


class JsonList[T](JsonBase[list[T]]):
    pass


class JsonDict[KT, VT](JsonBase[dict[KT, VT]]):
    pass
