from enum import Enum

from aiogram.utils.i18n import gettext as _


class RPSData(str, Enum):
    rock = "🪨"
    scissors = "✂"
    paper = "📜"

    @property
    def word(self) -> str:
        items = {
            self.rock: _("rock"),
            self.scissors: _("scissors"),
            self.paper: _("paper"),
        }

        return f'{self} {items[self]}'

    @property
    def resolve(self):
        items = {
            self.rock: self.scissors,
            self.scissors: self.paper,
            self.paper: self.rock,
        }

        return items.get(self)
