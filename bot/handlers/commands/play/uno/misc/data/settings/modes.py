from enum import Enum

from aiogram import types
from aiogram.utils.i18n import gettext as _

from .base import BaseUnoSettings


class UnoMode(int, Enum, BaseUnoSettings):
    FAST = 0
    WITH_POINTS = 1

    def __str__(self):
        match self:
            case self.FAST:
                return _('fast')
            case self.WITH_POINTS:
                return _('with points')

        raise TypeError(f'UnoMode: unexpected mode value: {self}')

    @classmethod
    def extract(cls, message: types.Message) -> "UnoMode":
        return cls.meta_extract(message, 1)
