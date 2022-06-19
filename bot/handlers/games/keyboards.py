from aiogram.dispatcher.filters.callback_data import CallbackData
from aiogram.utils.i18n import gettext as _, lazy_gettext as __
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder


class Games(CallbackData, prefix='game'):
    game: str
    value: str | None


def uno_start():
    builder = InlineKeyboardBuilder()

    builder.button(text=_("Yes"), callback_data=Games(game='uno', value='join'))
    builder.button(text=_("No"), callback_data=Games(game='uno', value='leave'))
    builder.button(text=_("Start UNO"), callback_data=Games(game='uno', value='start'))

    builder.adjust(2)
    return builder.as_markup()


def uno_show_cards():
    builder = InlineKeyboardBuilder()
    builder.button(text=_("Show maps"), switch_inline_query_current_chat="uno")
    return builder.as_markup()


def uno_color():
    from .uno.cards import UnoColors

    builder = ReplyKeyboardBuilder()

    for color in UnoColors.names(exclude={UnoColors.black}):
        builder.button(text=_("{emoji} {color} color").format(emoji=color.value, color=color.get_color()))

    builder.adjust(1)
    return builder.as_markup(
        resize_keyboard=True,
        selective=True,
        input_field_placeholder=_("What color will you choose?")
    )


UNO = __("UNO!")


def uno_uno():
    builder = ReplyKeyboardBuilder()
    builder.button(text=str(UNO))
    return builder.as_markup(
        resize_keyboard=True,
        input_field_placeholder=_("Add a card to your opponent's deck?")
    )


def get_rps_args() -> dict:
    return {
        ("🪨", _("Rock")): _("Scissors").lower(),
        ("✂", _("Scissors")): _("Paper").lower(),
        ("📜", _("Paper")): _("Rock").lower(),
    }


def rps_show_vars():
    builder = ReplyKeyboardBuilder()

    for item in get_rps_args():
        builder.button(text=' '.join(item))

    builder.adjust(1)
    return builder.as_markup(resize_keyboard=True, input_field_placeholder=_("What will you choose?"))
