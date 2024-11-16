import json
from typing import Self

from .base import BaseType


class JsonBase(BaseType[str]):
    @classmethod
    def __queryname__(cls) -> str:
        return "Json"

    @classmethod
    def deserialize(cls, value: str) -> Self:
        return cls(json.loads(value))  # type: ignore[args]

    def serialize(self) -> str:
        return json.dumps(self)


class JsonList[T](list[T], JsonBase):
    pass


class JsonDict[KT, VT](dict[KT, VT], JsonBase):
    pass
