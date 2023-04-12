from enum import Enum

from aiogram.utils.i18n import gettext as _


class RPSValues(str, Enum):
    ROCK = "🪨"
    SCISSORS = "✂"
    PAPER = "📜"

    def __str__(self) -> str:
        match self:
            case self.ROCK:
                item = _("rock")
            case self.SCISSORS:
                item = _("scissors")
            case self.PAPER:
                item = _("paper")
            case _:
                raise TypeError(f'RPSData: unexpected rps value: {self}')

        return f'{self.value} {item.capitalize()}'

    @property
    def resolve(self):
        match self:
            case self.ROCK:
                return self.SCISSORS
            case self.SCISSORS:
                return self.PAPER
            case self.PAPER:
                return self.ROCK

        raise TypeError(f'RPSData: unexpected rps value: {self}')
