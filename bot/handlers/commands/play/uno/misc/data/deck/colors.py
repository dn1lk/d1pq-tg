from collections.abc import Generator
from enum import Enum, EnumMeta
from typing import TypeVar

from aiogram.utils.i18n import gettext as _

T = TypeVar("T", "UnoColors", "Enum")


class UnoColorsMeta(EnumMeta):
    def exclude(cls: type[T], *excludes: T) -> Generator[T, None, None]:
        for color in cls:
            if color in excludes:
                continue
            yield color


class UnoColors(str, Enum, metaclass=UnoColorsMeta):
    BLUE = "🔵"
    GREEN = "🟢"
    RED = "🔴"
    YELLOW = "🟡"

    BLACK = "⚫"

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
                msg = f"{self.__class__.__name__}: unexpected value: {self}"
                raise TypeError(msg)

        return f"{self.value} {color}"
