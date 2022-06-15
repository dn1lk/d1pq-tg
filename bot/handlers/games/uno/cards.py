from enum import Enum, EnumMeta

from aiogram import types, Bot
from aiogram.utils.i18n import lazy_gettext as __
from pydantic import BaseModel


class UnoEnumMeta(EnumMeta):
    def __getitem__(cls, item):
        try:
            return cls._member_map_[item]
        except KeyError:
            for member in cls:
                if item in member.value:
                    return member

    def tuple(cls):
        return tuple(cls)[:-1]


class UnoColors(Enum, metaclass=UnoEnumMeta):
    blue = '🔵', __('blue')
    green = '🟢', __('green')
    red = '🔴', __('red')
    yellow = '🟡', __('yellow')

    special = '⚫', __('special')


class UnoSpecials(BaseModel):
    draw: int = 0
    color: bool | None
    skip: bool | types.User | None
    reverse: bool | None


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
    color=UnoColors.special,
    special=UnoSpecials()
)


def check_value_card(color: UnoColors, emoji: str) -> dict:
    specials = {
        '➕': UnoSpecials(
            skip=True,
            **{'draw': 4, 'color': True} if color == UnoColors.special else {'draw': 2}
        ),
        '🏳️\u200d🌈': UnoSpecials(color=True),
        '🚫': UnoSpecials(skip=True),
        '🔃': UnoSpecials(reverse=True),
    }

    return {
        'special': specials.get(emoji, UnoSpecials()),
        'emoji': emoji
    }


async def get_cards(bot: Bot) -> tuple[UnoCard]:
    def get(stickers: list[types.Sticker]):
        for sticker in stickers[8:10]:
            color = UnoColors.special
            stickers.remove(sticker)

            yield UnoCard(
                id=sticker.file_unique_id,
                file_id=sticker.file_id,
                color=color,
                **check_value_card(color, sticker.emoji)
            )

        for enum, color in enumerate(UnoColors.tuple()):
            for sticker in stickers[enum::4]:
                yield UnoCard(
                    id=sticker.file_unique_id,
                    file_id=sticker.file_id,
                    color=color,
                    **check_value_card(color, sticker.emoji)
                )

    return tuple(get((await bot.get_sticker_set('uno_cards')).stickers))
