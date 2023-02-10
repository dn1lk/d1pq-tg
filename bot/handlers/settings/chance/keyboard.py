from .. import Settings
from ..keyboard import *


class ChanceKeyboard(CallbackData, prefix=Settings.CHANCE.value):
    value: int


def chance(markov_chance: int | float):
    builder = InlineKeyboardBuilder()

    for i in 6, 10:
        math = round(markov_chance / i, 2)

        if markov_chance > 5:
            builder.button(
                text=f'-{math}',
                callback_data=ChanceKeyboard(value=markov_chance - math)
            )

        if markov_chance < 90:
            builder.button(
                text=f'+{math}',
                callback_data=ChanceKeyboard(value=markov_chance + math)
            )

    back(builder)
    builder.adjust(2)
    return builder.as_markup()
