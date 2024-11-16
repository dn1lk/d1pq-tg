from enum import EnumMeta, IntEnum
from typing import Self

from aiogram import types


class UnoSettingsMeta(EnumMeta):
    def meta_extract(cls, message: types.Message, index: int) -> "UnoSettingsMeta":
        assert message.text is not None, "wrong text"
        assert message.entities is not None, "wrong entities"

        entity_extracted = message.entities[1 + index].extract_from(message.text)
        for enum in cls:
            if str(enum) == entity_extracted:
                return enum

        raise ValueError


class UnoSettingsEnum(IntEnum, metaclass=UnoSettingsMeta):
    @property
    def next(self) -> Self:
        enums = tuple(self.__class__)
        return enums[(enums.index(self) + 1) % len(enums)]
