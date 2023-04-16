from aiogram import types
from aiogram.utils.i18n import gettext as _

from .base import UnoSettingsEnum


class UnoAddState(str, UnoSettingsEnum):
    OFF = 'off'
    ON = 'on'

    def __str__(self) -> str:
        match self:
            case self.OFF:
                return _("disabled")
            case self.ON:
                return _("enabled")

        raise TypeError(f'UnoAddState: unexpected additional value: {self}')

    @property
    def button(self) -> str:
        match self:
            case self.OFF:
                return _("Enable")
            case self.ON:
                return _("Disable")

        raise TypeError(f'UnoAddState: unexpected switcher value: {self}')

    @classmethod
    def extract(cls, message: types.Message, index: int) -> "UnoAddState":
        return cls.meta_extract(message, index)


class UnoAdd(int, UnoSettingsEnum):
    STACKING = 2
    SEVEN_0 = 3
    JUMP_IN = 4

    def __str__(self) -> str:
        match self:
            case self.STACKING:
                return _('Stacking')
            case self.SEVEN_0:
                return _('Seven-0')
            case self.JUMP_IN:
                return _('Jump-in')

    def extract(self, message: types.Message):
        if not self.value:
            raise TypeError()

        return UnoAddState.extract(message, self.value)
