from enum import Enum

from aiogram.utils.i18n import gettext as _


class RPSData(str, Enum):
    ROCK = "🪨"
    SCISSORS = "✂"
    PAPER = "📜"

    @property
    def word(self) -> str:
        match self:
            case self.ROCK:
                item = _("rock")
            case self.SCISSORS:
                item = _("scissors")
            case _:
                item = _("paper")

        return f'{self} {item.capitalize()}'

    @property
    def resolve(self):
        match self:
            case self.ROCK:
                return self.SCISSORS
            case self.SCISSORS:
                return self.PAPER
            case _:
                return self.ROCK
