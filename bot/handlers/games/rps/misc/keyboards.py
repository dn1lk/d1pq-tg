from aiogram.filters.callback_data import CallbackData
from aiogram.utils.keyboard import InlineKeyboardBuilder

from .data import RPSData


class RPSKeyboard(CallbackData, prefix='rps'):
    var: RPSData


def show_vars():
    from .data import RPSData

    builder = InlineKeyboardBuilder()

    for var in RPSData:
        builder.button(text=var.word, callback_data=RPSKeyboard(var=var))

    builder.adjust(1)
    return builder.as_markup()
