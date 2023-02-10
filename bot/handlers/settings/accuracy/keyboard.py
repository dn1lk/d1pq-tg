from .. import Settings
from ..keyboard import *


class AccuracyKeyboard(CallbackData, prefix=Settings.ACCURACY.value):
    value: int


def accuracy(markov_state: int):
    builder = InlineKeyboardBuilder()

    for i in range(1, 5):
        if i != markov_state:
            builder.button(text=str(i), callback_data=AccuracyKeyboard(value=i))

    back(builder)
    builder.adjust(3, 1)
    return builder.as_markup()
