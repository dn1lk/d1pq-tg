from typing import Self

from aiogram import types
from aiogram.utils.i18n import gettext as _

from .base import UnoSettingsEnum


class UnoDifficulty(UnoSettingsEnum):
    EASY = 3
    NORMAL = 2
    HARD = 1

    def __str__(self) -> str:
        match self:
            case self.EASY:
                difficulty = _("slowpoke")
            case self.NORMAL:
                difficulty = _("common man")
            case self.HARD:
                difficulty = _("genius")
            case _:
                msg = f"{self.__class__.__name__}: unexpected value: {self}"
                raise TypeError(msg)

        return difficulty

    @classmethod
    def extract(cls, message: types.Message) -> Self:
        return cls.meta_extract(message, 0)
