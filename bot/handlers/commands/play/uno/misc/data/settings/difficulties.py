from aiogram import types
from aiogram.utils.i18n import gettext as _

from .base import UnoSettingsEnum


class UnoDifficulty(int, UnoSettingsEnum):
    EASY = 3
    NORMAL = 2
    HARD = 1

    def __str__(self):
        match self:
            case self.EASY:
                return _('slowpoke')
            case self.NORMAL:
                return _('common man')
            case self.HARD:
                return _('genius')

        raise TypeError(f'UnoDifficulty: unexpected difficulty value: {self}')

    @classmethod
    def extract(cls, message: types.Message) -> "UnoDifficulty":
        return cls.meta_extract(message, 0)
