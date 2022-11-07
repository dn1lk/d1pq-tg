from aiogram import types
from aiogram.filters.callback_data import CallbackData
from aiogram.utils.i18n import gettext as _
from aiogram.utils.keyboard import InlineKeyboardBuilder


class UnoKeyboard(CallbackData, prefix='uno'):
    action: str
    value: int = None


def start():
    builder = InlineKeyboardBuilder()

    builder.button(text=_("Yes"), callback_data=UnoKeyboard(action='join'))
    builder.button(text=_("No"), callback_data=UnoKeyboard(action='leave'))
    builder.button(text=_("Settings"), callback_data=UnoKeyboard(action='settings'))
    builder.button(text=_("LET'S PLAY!"), callback_data=UnoKeyboard(action='start'))

    builder.adjust(2, 1)
    return builder.as_markup()


def settings(message: types.Message):
    from ..settings import UnoDifficulty, UnoMode, UnoAdd

    builder = InlineKeyboardBuilder()

    current_difficulty = UnoDifficulty.extract(message)

    for difficulty in UnoDifficulty:
        if difficulty is not current_difficulty:
            builder.button(
                text=difficulty.word.capitalize(),
                callback_data=UnoKeyboard(action=difficulty.name)
            )

    current_mode = UnoMode.extract(message)

    for mode in UnoMode:
        if mode is not current_mode:
            builder.button(text=mode.word.capitalize(), callback_data=UnoKeyboard(action=mode.name))

    for enum, name in enumerate(UnoAdd.get_names()):
        change_add = UnoAdd.off if UnoAdd.extract(message, enum) else UnoAdd.on
        builder.button(
            text=f'{change_add.switcher} {name.lower()}',
            callback_data=UnoKeyboard(action=change_add.name, value=enum)
        )

    builder.button(text=_("Back"), callback_data=UnoKeyboard(action='back'))

    builder.adjust(2, 1)
    return builder.as_markup()


def show_cards(bluffed: bool):
    builder = InlineKeyboardBuilder()

    if bluffed:
        builder.button(text=_("Bluff!"), callback_data=UnoKeyboard(action='bluff'))

    builder.button(text=_("Show cards"), switch_inline_query_current_chat="uno")

    builder.adjust(1)
    return builder.as_markup()


def choice_color():
    from . import UnoColors

    builder = InlineKeyboardBuilder()

    for color in UnoColors.get_colors(exclude={UnoColors.black}):
        builder.button(text=color.word, callback_data=UnoKeyboard(action=color.name))

    builder.adjust(1)
    return builder.as_markup()


def say_uno():
    from .bot import UNO

    builder = InlineKeyboardBuilder()
    builder.button(text=UNO, callback_data=UnoKeyboard(action='uno'))
    return builder.as_markup()
