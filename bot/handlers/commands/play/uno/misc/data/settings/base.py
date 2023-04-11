from enum import EnumMeta

from aiogram import types


class UnoSettingsMeta(EnumMeta):
    def meta_extract(cls, message: types.Message, index: int):
        entity = message.entities[1 + index]

        for enum in cls:
            if str(enum) == entity.extract_from(message.text):
                return enum


class BaseUnoSettings(metaclass=UnoSettingsMeta):
    @property
    def next(self):
        enums = tuple(self.__class__)
        return enums[(enums.index(self) + 1) % len(enums)]
