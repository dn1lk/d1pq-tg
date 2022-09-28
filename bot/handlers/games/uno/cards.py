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

    def names(cls, exclude: set = None):
        if exclude:
            return (color for color in cls.names() if color not in exclude)
        return cls


class UnoColors(str, Enum, metaclass=UnoColorsMeta):
    blue = '🔵'
    green = '🟢'
    red = '🔴'
    yellow = '🟡'

    black = '⚫'

    def get_color_name(self) -> str:
        colors = {
            self.blue: _("Blue"),
            self.green: _("Green"),
            self.red: _('Red'),
            self.yellow: _('Yellow'),
            self.black: _('Black'),
        }

        return colors.get(self)


class UnoSpecials(int, Enum):
    none = 0

    reverse = 1
    color = 2
    skip = 3
    draw = 4


class UnoCard(BaseModel):
    id: str
    file_id: str
    emoji: str

    color: UnoColors
    special: UnoSpecials


def check_special_card(emoji: str) -> UnoSpecials:
    specials = {
        '🔃': UnoSpecials.reverse,
        '🏳️\u200d🌈': UnoSpecials.color,
        '🚫': UnoSpecials.skip,
        '➕': UnoSpecials.draw,
    }

    return specials.get(emoji, UnoSpecials.none)


async def get_cards(bot: Bot) -> tuple[UnoCard]:
    def get(stickers: list[types.Sticker]):
        for sticker in stickers[8:10]:
            stickers.remove(sticker)

            yield UnoCard(
                id=sticker.file_unique_id,
                file_id=sticker.file_id,
                emoji=sticker.emoji,
                color=UnoColors.black,
                special=check_special_card(sticker.emoji)
            )

        for enum, color in enumerate(UnoColors.names(exclude={UnoColors.black})):
            for sticker in stickers[enum::4]:
                yield UnoCard(
                    id=sticker.file_unique_id,
                    file_id=sticker.file_id,
                    emoji=sticker.emoji,
                    color=color,
                    special=check_special_card(sticker.emoji)
                )

    return tuple(get((await bot.get_sticker_set('uno_cards')).stickers))
