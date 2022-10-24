from aiogram import types
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


def uno_settings(message: types.Message):
    from .uno.settings import UnoDifficulty, UnoMode, extract_current_difficulty, extract_current_mode

    builder = InlineKeyboardBuilder()

    current_difficulty = extract_current_difficulty(message)

    for difficulty in UnoDifficulty:
        if difficulty is not current_difficulty:
            builder.button(text=difficulty.word.capitalize(), callback_data=Games(game='uno', value=difficulty.name))

    current_mode = extract_current_mode(message)

    for mode in UnoMode:
        if mode is not current_mode:
            builder.button(text=mode.word.capitalize(), callback_data=Games(game='uno', value=mode.name))

    builder.button(text=_("Back"), callback_data=Games(game='uno', value='back'))

    builder.adjust(2, 1)
    return builder.as_markup()


def uno_show_cards(current_card: "UnoCard"):
    from .uno.process import UnoEmoji

    builder = InlineKeyboardBuilder()

    if current_card and current_card.cost == 50 and current_card.emoji is UnoEmoji.draw:
        builder.button(text=_("Check black card"), callback_data=Games(game='uno', value='check_draw_black_card'))

    builder.button(text=_("Show cards"), switch_inline_query_current_chat="uno")

    builder.adjust(1)
    return builder.as_markup()


def uno_color():
    from .uno.process import UnoColors

    builder = InlineKeyboardBuilder()

    for color in UnoColors.get_colors(exclude={UnoColors.black}):
        builder.button(
            text=color.word,
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
    from .rps import RPSVars

    builder = InlineKeyboardBuilder()

    for item in RPSVars:
        builder.button(text=item.word, callback_data=Games(game='rps', value=item))

    builder.adjust(1)
    return builder.as_markup()
