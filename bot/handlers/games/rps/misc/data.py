from enum import StrEnum

from aiogram.utils.i18n import gettext as _


class RPSData(StrEnum):
    ROCK = "🪨"
    SCISSORS = "✂"
    PAPER = "📜"

    @property
    def word(self) -> str | None:
        match self:
            case self.ROCK:
                item = _("rock")
            case self.SCISSORS:
                item = _("scissors")
            case self.PAPER:
                item = _("paper")
            case _:
                return

        return f'{self} {item}'

    @property
    def resolve(self):
        match self:
            case self.ROCK:
                return self.SCISSORS
            case self.SCISSORS:
                return self.PAPER
            case self.PAPER:
                return self.ROCK
