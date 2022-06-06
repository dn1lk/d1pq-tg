from typing import Optional, Union

from aiogram import types
from pydantic import BaseModel


class Colors(BaseModel):
    blue: str = 'blue'
    green: str = 'green'
    red: str = 'red'
    yellow: str = 'yellow'

    special: str = 'special'


colors = Colors()


class Specials(BaseModel):
    draw: str = 'draw'
    color: str = 'color'
    skip: str = 'skip'
    reverse: str = 'reverse'


specials = Specials()


BLUE_CARDS = {
    'AgADDAAD1XH9MQ': 0,
    'AgADEAAD1XH9MQ': 1,
    'AgADFAAD1XH9MQ': 2,
    'AgADGAAD1XH9MQ': 3,
    'AgADHAAD1XH9MQ': 4,
    'AgADIAAD1XH9MQ': 5,
    'AgADJAAD1XH9MQ': 6,
    'AgADKAAD1XH9MQ': 7,
    'AgADLAAD1XH9MQ': 8,
    'AgADMAAD1XH9MQ': 9,
    'AgADNAAD1XH9MQ': specials.draw,
    'AgADBgAD1XH9MQ': specials.skip,
    'AgADAgAD1XH9MQ': specials.reverse,
}

GREEN_CARDS = {
    'AgADDQAD1XH9MQ': 0,
    'AgADEQAD1XH9MQ': 1,
    'AgADFQAD1XH9MQ': 2,
    'AgADGQAD1XH9MQ': 3,
    'AgADHQAD1XH9MQ': 4,
    'AgADIQAD1XH9MQ': 5,
    'AgADJQAD1XH9MQ': 6,
    'AgADKQAD1XH9MQ': 7,
    'AgADLQAD1XH9MQ': 8,
    'AgADMQAD1XH9MQ': 9,
    'AgADNQAD1XH9MQ': specials.draw,
    'AgADBwAD1XH9MQ': specials.skip,
    'AgADAwAD1XH9MQ': specials.reverse,
}

RED_CARDS = {
    'AgADDgAD1XH9MQ': 0,
    'AgADEgAD1XH9MQ': 1,
    'AgADFgAD1XH9MQ': 2,
    'AgADGgAD1XH9MQ': 3,
    'AgADHgAD1XH9MQ': 4,
    'AgADIgAD1XH9MQ': 5,
    'AgADJgAD1XH9MQ': 6,
    'AgADKgAD1XH9MQ': 7,
    'AgADLgAD1XH9MQ': 8,
    'AgADMgAD1XH9MQ': 9,
    'AgADNgAD1XH9MQ': specials.draw,
    'AgADCAAD1XH9MQ': specials.skip,
    'AgADBAAD1XH9MQ': specials.reverse,
}

YELLOW_CARDS = {
    'AgADDwAD1XH9MQ': 0,
    'AgADEwAD1XH9MQ': 1,
    'AgADFwAD1XH9MQ': 2,
    'AgADGwAD1XH9MQ': 3,
    'AgADHwAD1XH9MQ': 4,
    'AgADIwAD1XH9MQ': 5,
    'AgADJwAD1XH9MQ': 6,
    'AgADKwAD1XH9MQ': 7,
    'AgADLwAD1XH9MQ': 8,
    'AgADMwAD1XH9MQ': 9,
    'AgADNwAD1XH9MQ': specials.draw,
    'AgADCQAD1XH9MQ': specials.skip,
    'AgADBQAD1XH9MQ': specials.reverse,
}

SPECIAL_CARDS = {
    'AgADCwAD1XH9MQ': specials.draw,
    'AgADCgAD1XH9MQ': specials.color,
}


ALL_CARDS = tuple(
    zip(
        (
            BLUE_CARDS,
            GREEN_CARDS,
            RED_CARDS,
            YELLOW_CARDS,
            SPECIAL_CARDS
        ),
        tuple(colors.dict())
    )
)


class UnoCard(BaseModel):
    id: str
    color: str
    number: Optional[int]
    special: Optional[str]


class UnoSticker(BaseModel):
    file_unique_id: str
    file_id: str


def check_value_card(value: Union[int, str]) -> dict:
    if isinstance(value, int):
        return {'number': value}
    else:
        return {'special': value}


def get_cards():
    for cards, color in ALL_CARDS:
        for card_id, value in cards.items():
            yield UnoCard(id=card_id, color=color, **check_value_card(value))


def get_card(card: UnoSticker):
    for cards, color in ALL_CARDS:
        try:
            value = cards[card.file_unique_id]
            return UnoCard(id=card.file_unique_id, color=color, **check_value_card(value))
        except KeyError:
            continue


def get_sticker(sticker: types.Sticker):
    return UnoSticker(file_unique_id=sticker.file_unique_id, file_id=sticker.file_id)
