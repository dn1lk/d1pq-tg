from enum import Enum

from aiogram import types
from aiogram.filters.callback_data import CallbackData
from aiogram.utils.i18n import gettext as _
from aiogram.utils.keyboard import InlineKeyboardBuilder

from .data.deck.colors import UnoColors
from .data.settings.additions import UnoAdd, UnoAddState
from ...misc.actions import PlayActions


class UnoSetup(str, Enum):
    JOIN = 'join'
    LEAVE = 'leave'
    SETTINGS = 'settings'
    START = 'start'

    def __str__(self):
        match self:
            case self.JOIN:
                return _("Yes")
            case self.LEAVE:
                return _("No")
            case self.SETTINGS:
                return _("Settings")
            case self.START:
                return _("LET'S PLAY!")

        raise TypeError(f'UnoSetup: unexpected action: {self}')


class UnoSettings(str, Enum):
    DIFFICULTY = 'difficulty'
    MODE = 'mode'

    def __str__(self):
        match self:
            case self.DIFFICULTY:
                return _("difficulty")
            case self.MODE:
                return _("mode")

        raise TypeError(f'UnoSettings: unexpected setting: {self}')


class UnoActions(str, Enum):
    BLUFF = 'bluff'
    COLOR = 'color'
    UNO = 'uno'

    BACK = 'back'

    def __str__(self):
        match self:
            case self.BACK:
                return _("Back")

        raise TypeError(f'UnoActions: unexpected action: {self}')


class UnoData(CallbackData, prefix=PlayActions.UNO[0]):
    action: UnoActions | UnoSetup | UnoSettings | UnoAdd
    value: UnoAddState | UnoColors = None


def setup_keyboard():
    builder = InlineKeyboardBuilder()

    for action in UnoSetup:
        builder.button(text=str(action), callback_data=UnoData(action=action))

    builder.adjust(2, 1)
    return builder.as_markup()


def settings_keyboard(message: types.Message):
    builder = InlineKeyboardBuilder()

    for action in UnoSettings:
        builder.button(
            text=_("Change {settings}".format(settings=str(action))),
            callback_data=UnoData(action=action)
        )

    for add in UnoAdd:
        add_state = add.extract(message)
        builder.button(
            text=f'{add_state.button} {str(add).lower()}',
            callback_data=UnoData(action=add, value=add_state)
        )

    builder.button(
        text=str(UnoActions.BACK),
        callback_data=UnoData(action=UnoActions.BACK)
    )

    builder.adjust(1)
    return builder.as_markup()


def show_cards(is_draw_four: bool):
    builder = InlineKeyboardBuilder()

    if is_draw_four:
        builder.button(text=_("Bluff!"), callback_data=UnoData(action=UnoActions.BLUFF))

    builder.button(text=_("Show cards"), switch_inline_query_current_chat="uno")

    builder.adjust(1)
    return builder.as_markup()


def choice_color():
    builder = InlineKeyboardBuilder()

    for color in UnoColors.exclude(UnoColors.BLACK):
        builder.button(text=color, callback_data=UnoData(action=UnoActions.COLOR, value=color))

    builder.adjust(1)
    return builder.as_markup()


def say_uno():
    builder = InlineKeyboardBuilder()

    from .actions.bot import UNO
    builder.button(text=UNO, callback_data=UnoData(action=UnoActions.UNO))

    return builder.as_markup()
