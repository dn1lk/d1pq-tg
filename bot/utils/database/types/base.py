from typing import Self


class BaseType[T]:
    @classmethod
    def __queryname__(cls) -> str:
        return cls.__name__

    def __setattr__(self, name: str, value: T) -> None:
        return super().__setattr__(name, value)

    @classmethod
    def deserialize(cls, *args, **kwargs) -> Self:
        return cls(*args, **kwargs)

    def serialize(self) -> T | Self:
        return self
