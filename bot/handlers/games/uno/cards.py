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

    def get_names(cls, exclude: set = None):
        if exclude:
            return (color for color in cls.get_names() if color not in exclude)
        return cls


class UnoColors(str, Enum, metaclass=UnoColorsMeta):
    blue = '🔵'
    green = '🟢'
    red = '🔴'
    yellow = '🟡'

    black = '⚫'

    @property
    def name(self) -> str:
        colors = {
            self.blue: _("Blue"),
            self.green: _("Green"),
            self.red: _('Red'),
            self.yellow: _('Yellow'),
            self.black: _('Black'),
        }

        return colors.get(self)


class UnoEmoji(str, Enum):
    none = 'Null'

    reverse = '🔃'
    color = '🏳️\u200d🌈'
    skip = '🚫'
    draw = '➕'


class UnoCard(BaseModel):
    id: str
    file_id: str
    emoji: str

    color: UnoColors


async def get_cards(bot: Bot) -> tuple[UnoCard]:
    def get(stickers: list[types.Sticker]):
        for sticker in stickers[8:10]:
            stickers.remove(sticker)

            yield UnoCard(
                id=sticker.file_unique_id,
                file_id=sticker.file_id,
                emoji=sticker.emoji,
                color=UnoColors.black,
            )

        for enum, color in enumerate(UnoColors.get_names(exclude={UnoColors.black})):
            for sticker in stickers[enum::4]:
                yield UnoCard(
                    id=sticker.file_unique_id,
                    file_id=sticker.file_id,
                    emoji=sticker.emoji,
                    color=color,
                )

    return tuple(get((await bot.get_sticker_set('uno_cards')).stickers))
