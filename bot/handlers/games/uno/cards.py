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

    def names(cls):
        return tuple(cls)[:-1]


class UnoColors(str, Enum, metaclass=UnoColorsMeta):
    blue = '🔵'
    green = '🟢'
    red = '🔴'
    yellow = '🟡'

    black = '⚫'

    def get_color(self):
        colors = {
            self.blue: _("Blue"),
            self.green: _("Green"),
            self.red: _('Red'),
            self.yellow: _('Yellow'),
            self.black: _('Black'),
        }

        return colors.get(self)


class UnoSpecials(BaseModel):
    draw: int = 0
    color: bool = False
    skip: bool | types.User = False
    reverse: bool = False


class UnoCard(BaseModel):
    id: str
    file_id: str
    emoji: str

    color: UnoColors
    special: UnoSpecials


draw_card = UnoCard(
    id='AgADlhYAAtYJCUk',
    file_id='CAACAgIAAxkBAAJ99mKgyaLsi0LGnwOdUI_DhzgN7H1CAAKWFgAC1gkJSZxwlQOpRW3PJAQ',
    emoji='➕',
    color=UnoColors.black,
    special=UnoSpecials(),
)


def check_special_card(color: UnoColors, emoji: str) -> dict[str, UnoSpecials]:
    specials = {
        '➕': UnoSpecials(
            skip=True,
            **{'draw': 4, 'color': True} if color is UnoColors.black else {'draw': 2}
        ),
        '🏳️\u200d🌈': UnoSpecials(color=True),
        '🚫': UnoSpecials(skip=True),
        '🔃': UnoSpecials(reverse=True),
    }

    return {'special': specials.get(emoji, UnoSpecials())}


async def get_cards(bot: Bot) -> tuple[UnoCard]:
    def get(stickers: list[types.Sticker]):
        for sticker in stickers[8:10]:
            color = UnoColors.black
            stickers.remove(sticker)

            yield UnoCard(
                id=sticker.file_unique_id,
                file_id=sticker.file_id,
                color=color,
                emoji=sticker.emoji,
                **check_special_card(color, sticker.emoji)
            )

        for enum, color in enumerate(UnoColors.names()):
            for sticker in stickers[enum::4]:
                yield UnoCard(
                    id=sticker.file_unique_id,
                    file_id=sticker.file_id,
                    color=color,
                    emoji=sticker.emoji,
                    **check_special_card(color, sticker.emoji)
                )

    return tuple(get((await bot.get_sticker_set('uno_cards')).stickers))
