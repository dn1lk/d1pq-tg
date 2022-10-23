from enum import Enum

from aiogram import types, Bot
from aiogram.utils.i18n import gettext as _
from pydantic import BaseModel


class UnoColors(int, Enum):
    blue = 0
    green = 1
    red = 2
    yellow = 3

    black = 4

    @property
    def word(self) -> str:
        colors = {
            self.blue: "🔵" + " " + _("Blue"),
            self.green: "🟢" + " " + _("Green"),
            self.red: "🔴" + " " + _("Red"),
            self.yellow: "🟡" + " " + _("Yellow"),
            self.black: "⚫" + " " + _("Black"),
        }

        return colors[self]


class UnoEmoji(str, Enum):
    reverse = '🔃'
    skip = '🚫'
    color = '🌈'
    draw = '➕'


class UnoCard(BaseModel):
    file_unique_id: str
    file_id: str
    emoji: str

    color: UnoColors
    cost: int


async def get_cards(bot: Bot) -> list[UnoCard]:
    def get(stickers: list[types.Sticker]):
        for color in tuple(UnoColors)[:-1]:
            for cost, sticker in enumerate(stickers[color.value:-3:4]):
                yield UnoCard(
                    file_unique_id=sticker.file_unique_id,
                    file_id=sticker.file_id,
                    emoji=sticker.emoji,
                    color=color,
                    cost=cost if cost < 10 else 20
                )

        for sticker in stickers[-2:]:
            yield UnoCard(
                file_unique_id=sticker.file_unique_id,
                file_id=sticker.file_id,
                emoji=sticker.emoji,
                color=UnoColors.black,
                cost=50,
            )

    cards = list(get((await bot.get_sticker_set('uno_by_bp1lh_bot')).stickers))
    cards.extend([card for card in cards if card.cost != 0])

    return cards
