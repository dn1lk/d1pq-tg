from aiogram import types
from aiogram.filters.callback_data import CallbackData
from aiogram.utils.i18n import gettext as _
from aiogram.utils.keyboard import InlineKeyboardBuilder


class Games(CallbackData, prefix='game'):
    game: str
    value: str


class UnoGame(Games, prefix='game'):
    game: str = 'uno'
    index: int = None


def uno_start():
    builder = InlineKeyboardBuilder()

    builder.button(text=_("Yes"), callback_data=UnoGame(value='join'))
    builder.button(text=_("No"), callback_data=UnoGame(value='leave'))
    builder.button(text=_("Settings"), callback_data=UnoGame(value='settings'))
    builder.button(text=_("LET'S PLAY!"), callback_data=UnoGame(value='start'))

    builder.adjust(2, 1)
    return builder.as_markup()


def uno_settings(message: types.Message):
    from .uno.settings import UnoDifficulty, UnoMode, UnoAdd

    builder = InlineKeyboardBuilder()

    current_difficulty = UnoDifficulty.extract(message)

    for difficulty in UnoDifficulty:
        if difficulty is not current_difficulty:
            builder.button(
                text=difficulty.word.capitalize(),
                callback_data=UnoGame(value=difficulty.name)
            )

    current_mode = UnoMode.extract(message)

    for mode in UnoMode:
        if mode is not current_mode:
            builder.button(text=mode.word.capitalize(), callback_data=UnoGame(value=mode.name))

    for enum, name in enumerate(UnoAdd.names()):
        change_add = UnoAdd.off if UnoAdd.extract(message, enum) else UnoAdd.on
        builder.button(
            text=f'{change_add.changer} {name.lower()}',
            callback_data=UnoGame(value=change_add.name, index=enum)
        )

    builder.button(text=_("Back"), callback_data=UnoGame(value='back'))

    builder.adjust(2, 1)
    return builder.as_markup()


def uno_show_cards(bluffed: int):
    builder = InlineKeyboardBuilder()

    if bluffed:
        builder.button(text=_("Bluff!"), callback_data=UnoGame(value='bluff'))

    builder.button(text=_("Show cards"), switch_inline_query_current_chat="uno")

    builder.adjust(1)
    return builder.as_markup()


def uno_color():
    from .uno.process import UnoColors

    builder = InlineKeyboardBuilder()

    for color in UnoColors.get_colors(exclude={UnoColors.black}):
        builder.button(text=color.word, callback_data=UnoGame(value=color))

    builder.adjust(1)
    return builder.as_markup()


def uno_say():
    from .uno.process.bot import UNO

    builder = InlineKeyboardBuilder()
    builder.button(text=UNO, callback_data=UnoGame(value='uno'))
    return builder.as_markup()


def rps_show_vars():
    from .rps import RPSVars

    builder = InlineKeyboardBuilder()

    for item in RPSVars:
        builder.button(text=item.word, callback_data=Games(game='rps', value=item))

    builder.adjust(1)
    return builder.as_markup()
