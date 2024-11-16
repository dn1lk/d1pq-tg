from aiogram import types
from aiogram.filters.callback_data import CallbackData
from aiogram.utils.keyboard import InlineKeyboardBuilder

from handlers.commands.play import PlayActions

from .values import RPSValues


class RPSData(CallbackData, prefix=PlayActions.RPS[0]):
    value: RPSValues


def rps_keyboard() -> types.InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    for value in RPSValues:
        builder.button(text=str(value), callback_data=RPSData(value=value))

    builder.adjust(1)
    return builder.as_markup()
