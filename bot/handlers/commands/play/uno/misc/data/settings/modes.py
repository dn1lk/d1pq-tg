from typing import Self

from aiogram import types
from aiogram.utils.i18n import gettext as _

from .base import UnoSettingsEnum


class UnoMode(UnoSettingsEnum):
    FAST = 0
    WITH_POINTS = 1

    def __str__(self) -> str:
        match self:
            case self.FAST:
                mode = _("fast")
            case self.WITH_POINTS:
                mode = _("with points")
            case _:
                msg = f"{self.__class__.__name__}: unexpected value: {self}"
                raise TypeError(msg)

        return mode

    @classmethod
    def extract(cls, message: types.Message) -> Self:
        return cls.meta_extract(message, 1)
