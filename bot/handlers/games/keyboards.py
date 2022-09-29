from aiogram.filters.callback_data import CallbackData
from aiogram.utils.i18n import gettext as _
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
    from .uno import UnoColors

    builder = InlineKeyboardBuilder()

    for color in UnoColors.get_names(exclude={UnoColors.black}):
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
