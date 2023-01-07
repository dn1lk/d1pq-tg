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
                if item in member.action:
                    return member

    def get_colors(cls, exclude: set = None):
        if exclude:
            return (color for color in cls.get_colors() if color not in exclude)
        return cls


class UnoColors(str, Enum, metaclass=UnoColorsMeta):
    BLUE = "🔵"
    GREEN = "🟢"
    RED = "🔴"
    YELLOW = "🟡"

    BLACK = "⚫"

    @property
    def word(self) -> str:
        match self:
            case self.BLUE:
                color = _("Blue")
            case self.GREEN:
                color = _("Green")
            case self.RED:
                color = _("Red")
            case self.YELLOW:
                color = _("Yellow")
            case _:
                color = _("Black")

        return f'{self} {color}'


class UnoEmoji(str, Enum):
    NULL = '0️⃣'
    SEVEN = '7️⃣'

    REVERSE = '🔃'
    SKIP = '🚫'
    COLOR = '🌈'
    DRAW_TWO = '➕'
    DRAW_FOUR = '✖'


class UnoCard(BaseModel):
    file_unique_id: str
    file_id: str
    emoji: str

    color: UnoColors
    cost: int

    def __radd__(self, other):
        return self.cost.__add__(other)


async def get_deck(bot: Bot) -> list[UnoCard]:
    def get(stickers: list[types.Sticker]):
        for enum, color in enumerate(UnoColors.get_colors(exclude={UnoColors.BLACK})):
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
                color=UnoColors.BLACK,
                cost=50,
            )

    deck = list(get((await bot.get_sticker_set('uno_by_bp1lh_bot')).stickers))
    deck.extend([card for card in deck if card.cost != 0])

    return deck
