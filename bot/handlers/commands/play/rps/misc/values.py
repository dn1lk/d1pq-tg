from enum import Enum

from aiogram.utils.i18n import gettext as _


class RPSValues(str, Enum):
    ROCK = "🪨"
    SCISSORS = "✂"
    PAPER = "📜"

    def __str__(self) -> str:
        match self:
            case self.ROCK:
                value = _("rock")
            case self.SCISSORS:
                value = _("scissors")
            case self.PAPER:
                value = _("paper")
            case _:
                msg = f"{self.__class__.__name__}: unexpected value: {self}"
                raise TypeError(msg)

        return f"{self.value} {value.capitalize()}"

    @property
    def resolve(self) -> "RPSValues":
        match self:
            case self.ROCK:
                resolve = self.SCISSORS
            case self.SCISSORS:
                resolve = self.PAPER
            case self.PAPER:
                resolve = self.ROCK
            case _:
                msg = f"{self.__class__.__name__}: unexpected value: {self}"
                raise TypeError(msg)

        return resolve
