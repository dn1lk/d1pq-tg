from aiogram.filters.callback_data import CallbackData
from aiogram.utils.i18n import gettext as _
from aiogram.utils.keyboard import InlineKeyboardBuilder


class Games(CallbackData, prefix='game'):
    game: str
    value: str | None


def uno_start():
    builder = InlineKeyboardBuilder()

    builder.button(text=_("Yes"), callback_data=Games(game='uno', value='join'))
    builder.button(text=_("No"), callback_data=Games(game='uno', value='leave'))
    builder.button(text=_("Settings"), callback_data=Games(game='uno', value='settings'))
    builder.button(text=_("LET'S PLAY!"), callback_data=Games(game='uno', value='start'))

    builder.adjust(2, 1)
    return builder.as_markup()


def uno_difficulty(current_difficulty: str):
    from .uno.settings import UnoDifficulty

    builder = InlineKeyboardBuilder()

    for difficulty in UnoDifficulty:
        if difficulty.name != current_difficulty:
            builder.button(text=difficulty.word.capitalize(), callback_data=Games(game='uno', value=difficulty))

    builder.button(text=_("Back"), callback_data=Games(game='uno', value='back'))

    builder.adjust(2)
    return builder.as_markup()


def uno_show_cards():
    builder = InlineKeyboardBuilder()
    builder.button(text=_("Show cards"), switch_inline_query_current_chat="uno")
    return builder.as_markup()


def uno_color():
    from .uno.process import UnoColors

    builder = InlineKeyboardBuilder()

    for color in tuple(UnoColors)[-1]:
        builder.button(
            text=color.value + ' ' + color.word,
            callback_data=Games(game='uno', value=color.value)
        )

    builder.adjust(1)
    return builder.as_markup()


def uno_uno():
    from .uno.process.bot import UNO

    builder = InlineKeyboardBuilder()
    builder.button(text=UNO, callback_data=Games(game='uno', value='uno'))
    return builder.as_markup()


def rps_show_vars():
    builder = InlineKeyboardBuilder()

    for item in RPSVars:
        builder.button(text=item.word, callback_data=Games(game='rps', value=item))

    builder.adjust(1)
    return builder.as_markup()
