from enum import Enum, EnumMeta
from typing import Generator

from aiogram.utils.i18n import gettext as _


class UnoColorsMeta(EnumMeta):
    def exclude(cls, *excludes: "UnoColors") -> Generator["UnoColors", None, None]:
        for color in cls:
            if color in excludes:
                continue
            yield color


class UnoColors(str, Enum, metaclass=UnoColorsMeta):
    BLUE = '🔵'
    GREEN = '🟢'
    RED = '🔴'
    YELLOW = '🟡'

    BLACK = '⚫'

    def __str__(self) -> str:
        match self:
            case self.BLUE:
                color = _("Blue")
            case self.GREEN:
                color = _("Green")
            case self.RED:
                color = _("Red")
            case self.YELLOW:
                color = _("Yellow")
            case self.BLACK:
                color = _("Black")
            case _:
                raise TypeError(f'UnoColors: unexpected card color: {self}')

        return f'{self.value} {color}'
