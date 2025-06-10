from aiogram import types
from aiogram.filters.callback_data import CallbackData
from aiogram.utils.i18n import gettext as _
from aiogram.utils.keyboard import InlineKeyboardBuilder

from handlers.commands import CommandTypes
from handlers.commands.settings.misc.keyboards import add_back_button

from .actions import RecordActions


class RecordData(CallbackData, prefix=f"{CommandTypes.SETTINGS[0]}_record"):
    action: RecordActions
    to_blocked: bool | None = None


def switch_keyboard(actions: dict[RecordActions, bool]) -> types.InlineKeyboardMarkup:
    text = _("{action} {field} recording")
    builder = InlineKeyboardBuilder()

    for action, is_enabled in actions.items():
        if is_enabled:
            _action = _("Disable")
            to_blocked = True
        else:
            _action = _("Enable")
            to_blocked = False

        builder.button(
            text=text.format(action=_action, field=action.keyboard.lower()),
            callback_data=RecordData(action=action, to_blocked=to_blocked),
        )

    builder.button(
        text=RecordActions.DELETE.keyboard,
        callback_data=RecordData(action=RecordActions.DELETE),
    )

    add_back_button(builder)

    builder.adjust(1)
    return builder.as_markup()
