from typing import Any, cast

type DBT = Any


class BaseType[CT]:
    @classmethod
    def __queryname__(cls) -> str:
        return cls.__name__

    @classmethod
    def deserialize(cls, value: DBT) -> CT:
        return cast("CT", value)

    @classmethod
    def serialize(cls, value: CT) -> DBT:
        return cast("DBT", value)
