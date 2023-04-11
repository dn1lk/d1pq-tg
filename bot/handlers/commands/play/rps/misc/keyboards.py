from aiogram.filters.callback_data import CallbackData
from aiogram.utils.keyboard import InlineKeyboardBuilder

from .values import RPSValues
from ... import PlayActions


class RPSData(CallbackData, prefix=PlayActions.RPS[0]):
    value: RPSValues


def rps_keyboard():
    builder = InlineKeyboardBuilder()

    for value in RPSValues:
        builder.button(text=value, callback_data=RPSData(value=value))

    builder.adjust(1)
    return builder.as_markup()
