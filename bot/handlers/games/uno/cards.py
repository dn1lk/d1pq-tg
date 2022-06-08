from enum import Enum, EnumMeta
from typing import Optional, List, Tuple, Union

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


class UnoDraw(BaseModel):
    user: Optional[types.User]
    amount: int


class UnoSpecials(BaseModel):
    draw: Optional[UnoDraw]
    color: Optional[bool]
    skip: Optional[Union[types.User, bool]]
    reverse: Optional[bool]


class UnoCard(BaseModel):
    id: str
    file_id: str
    emoji: str

    color: UnoColors
    special: UnoSpecials


DRAW_CARD = UnoCard(
    id='AgADlhYAAtYJCUk',
    file_id='CAACAgIAAxkBAAJ99mKgyaLsi0LGnwOdUI_DhzgN7H1CAAKWFgAC1gkJSZxwlQOpRW3PJAQ',
    emoji='➕',
    color=UnoColors.special,
    special=UnoSpecials()
)


def check_value_card(color: UnoColors, emoji: str) -> dict:
    specials = {
        '➕': UnoSpecials(
            **{'draw': UnoDraw(amount=4), 'color': True} if color == UnoColors.special else
            {'draw': UnoDraw(amount=2)}
        ),
        '🏳️\u200d🌈': UnoSpecials(color=True),
        '🚫': UnoSpecials(skip=True),
        '🔃': UnoSpecials(reverse=True),
    }

    return {
        'special': specials.get(emoji, UnoSpecials()),
        'emoji': emoji
    }


async def get_cards(bot: Bot) -> Tuple[UnoCard]:
    def get(stickers: List[types.Sticker]):
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
