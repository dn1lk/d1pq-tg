from enum import Enum, auto

from aiogram.filters.callback_data import CallbackData
from aiogram.utils.i18n import gettext as _
from aiogram.utils.keyboard import InlineKeyboardBuilder


class SettingsKeyboard(CallbackData, prefix='set'):
    action: Settings


def settings():
    builder = InlineKeyboardBuilder()

    for action in tuple(SettingsAction)[:5]:
        builder.button(text=action.word, callback_data=SettingsKeyboard(action=action))

    builder.adjust(1)
    return builder.as_markup()


def back(builder: InlineKeyboardBuilder):
    return builder.button(
        text=SettingsAction.BACK.word,
        callback_data=SettingsKeyboard(action=SettingsAction.BACK)
    )
