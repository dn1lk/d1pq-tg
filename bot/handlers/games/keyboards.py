from aiogram.filters.callback_data import CallbackData
from aiogram.utils.i18n import gettext as _
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder

from bot.handlers.settings.keyboards import back


class Games(CallbackData, prefix='game'):
    game: str
    value: str | None


def uno_start():
    builder = InlineKeyboardBuilder()

    builder.button(text=_("Yes"), callback_data=Games(game='uno', value='join'))
    builder.button(text=_("No"), callback_data=Games(game='uno', value='leave'))
    builder.button(text=_("Change difficulty"), callback_data=Games(game='uno', value='difficulty'))
    builder.button(text=_("LET'S PLAY!"), callback_data=Games(game='uno', value='start'))

    builder.adjust(2, 1)
    return builder.as_markup()


def get_uno_difficulties():
    return {_('low'): 0.3, _('medium'): 0.5, _('high'): 0.7}


def uno_difficulties(current_difficulty: str):
    difficulties = get_uno_difficulties()
    builder = InlineKeyboardBuilder()

    for difficulty, level in difficulties.items():
        if difficulty != current_difficulty:
            builder.button(text=difficulty.capitalize(), callback_data=Games(game='uno', value=difficulty))

    builder.button(text=_("Back"), callback_data=Games(game='uno', value='back'))

    builder.adjust(1)
    return builder.as_markup()


def uno_show_cards():
    builder = InlineKeyboardBuilder()
    builder.button(text=_("Show cards"), switch_inline_query_current_chat="uno")
    return builder.as_markup()


def uno_color():
    from .uno import UnoColors

    builder = InlineKeyboardBuilder()

    for color in UnoColors.get_colors(exclude={UnoColors.black}):
        builder.button(
            text=color.value + ' ' + color.name,
            callback_data=Games(game='uno', value=color.value)
        )

    builder.adjust(1)
    return builder.as_markup()


def uno_uno():
    from .uno import UNO

    builder = InlineKeyboardBuilder()
    builder.button(text=str(UNO), callback_data=Games(game='uno', value='uno'))
    return builder.as_markup()


def get_rps_args() -> dict:
    return {
        ("🪨", _("Rock")): _("Scissors"),
        ("✂", _("Scissors")): _("Paper"),
        ("📜", _("Paper")): _("Rock"),
    }


def rps_show_vars():
    builder = ReplyKeyboardBuilder()

    for item in get_rps_args():
        builder.button(text=' '.join(item))

    builder.adjust(1)
    return builder.as_markup(resize_keyboard=True, input_field_placeholder=_("What will you choose?"))
