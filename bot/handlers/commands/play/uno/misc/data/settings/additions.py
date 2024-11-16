from typing import Self

from aiogram import types
from aiogram.utils.i18n import gettext as _

from .base import UnoSettingsEnum


class UnoAddState(UnoSettingsEnum):
    OFF = 0
    ON = 1

    def __str__(self) -> str:
        match self:
            case self.OFF:
                state = _("disabled")
            case self.ON:
                state = _("enabled")
            case _:
                msg = f"{self.__class__.__name__}: unexpected value: {self}"
                raise TypeError(msg)

        return state

    @property
    def button(self) -> str:
        match self:
            case self.OFF:
                button = _("Enable")
            case self.ON:
                button = _("Disable")
            case _:
                msg = f"{self.__class__.__name__}: unexpected value: {self}"
                raise TypeError(msg)

        return button

    @classmethod
    def extract(cls, message: types.Message, index: int) -> Self:
        return cls.meta_extract(message, index)


class UnoAdd(UnoSettingsEnum):
    STACKING = 2
    SEVEN_0 = 3
    JUMP_IN = 4

    def __str__(self) -> str:
        match self:
            case self.STACKING:
                add = _("Stacking")
            case self.SEVEN_0:
                add = _("Seven-0")
            case self.JUMP_IN:
                add = _("Jump-in")
            case _:
                msg = f"{self.__class__.__name__}: unexpected value: {self}"
                raise TypeError(msg)

        return add

    def extract(self, message: types.Message) -> UnoAddState:
        return UnoAddState.extract(message, self.value)
