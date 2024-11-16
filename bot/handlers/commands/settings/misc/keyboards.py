from aiogram import types
from aiogram.filters.callback_data import CallbackData
from aiogram.utils.keyboard import InlineKeyboardBuilder

from handlers.commands import CommandTypes

from .actions import SettingsActions


class SettingsData(CallbackData, prefix=CommandTypes.SETTINGS[0]):
    action: SettingsActions
    value: str | None = None


def add_back_button(builder: InlineKeyboardBuilder) -> InlineKeyboardBuilder:
    return builder.button(
        text=SettingsActions.BACK.keyboard,
        callback_data=SettingsData(action=SettingsActions.BACK),
    )


def actions_keyboard() -> types.InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    for action in tuple(SettingsActions)[:-1]:
        builder.button(text=action.keyboard, callback_data=SettingsData(action=action))

    builder.adjust(1)
    return builder.as_markup()


def accuracy_keyboard(current_accuracy: int) -> types.InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    for accuracy in range(1, 5):
        if accuracy != current_accuracy:
            builder.button(
                text=str(accuracy),
                callback_data=SettingsData(action=SettingsActions.ACCURACY, value=f"{accuracy}"),
            )

    add_back_button(builder)

    builder.adjust(3)
    return builder.as_markup()


def chance_keyboard(current_chance: int) -> types.InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    for chance in range(0, 100, 10):
        if chance != current_chance:
            builder.button(
                text=f"{chance}%",
                callback_data=SettingsData(action=SettingsActions.CHANCE, value=f"{chance}"),
            )

    add_back_button(builder)

    builder.adjust(3)
    return builder.as_markup()


def locale_keyboard(locales: dict[str, str], current_locale: str) -> types.InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    for code, language in locales.items():
        if code != current_locale:
            builder.button(text=language, callback_data=SettingsData(action=SettingsActions.LOCALE, value=code))

    add_back_button(builder)

    builder.adjust(1)
    return builder.as_markup()
