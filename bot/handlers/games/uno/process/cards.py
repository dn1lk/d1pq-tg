from enum import Enum, EnumMeta

from aiogram import types, Bot
from aiogram.utils.i18n import gettext as _
from pydantic import BaseModel


class UnoColorsMeta(EnumMeta):
    def __getitem__(cls, item):
        if item in cls._member_map_:
            return cls._member_map_[item]
        else:
            for member in cls:
                if item in member.value:
                    return member

    def get_colors(cls, exclude: set = None):
        if exclude:
            return (color for color in cls.get_colors() if color not in exclude)
        return cls


class UnoColors(str, Enum, metaclass=UnoColorsMeta):
    blue = "🔵"
    green = "🟢"
    red = "🔴"
    yellow = "🟡"

    black = "⚫"

    @property
    def word(self) -> str:
        colors = {
            self.blue: self.blue.value + " " + _("Blue"),
            self.green: self.green.value + " " + _("Green"),
            self.red: self.red.value + " " + _("Red"),
            self.yellow: self.yellow.value + " " + _("Yellow"),
            self.black: self.black.value + " " + _("Black"),
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


async def get_deck(bot: Bot) -> list[UnoCard]:
    def get(stickers: list[types.Sticker]):
        for enum, color in enumerate(UnoColors.get_colors(exclude={UnoColors.black})):
            for cost, sticker in enumerate(stickers[enum:-3:4]):
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

    deck = list(get((await bot.get_sticker_set('uno_by_bp1lh_bot')).stickers))
    deck.extend([card for card in deck if card.cost != 0])

    return deck
