from enum import Enum, auto

from aiogram import types
from aiogram.filters.callback_data import CallbackData
from aiogram.utils.i18n import gettext as _
from aiogram.utils.keyboard import InlineKeyboardBuilder

from .cards import UnoColors
from .data import UnoAdd


class UnoActions(Enum):
    def _generate_next_value_(name, *args):
        return name.lower()

    JOIN = auto()
    LEAVE = auto()
    SETTINGS = auto()
    START = auto()

    DIFFICULTY = auto()
    MODE = auto()
    BACK = auto()

    BLUFF = auto()
    COLOR = auto()
    UNO = auto()

    @property
    def word(self) -> str:
        match self:
            case self.JOIN:
                return _("Yes")
            case self.LEAVE:
                return _("No")
            case self.SETTINGS:
                return _("Settings")
            case self.START:
                return _("LET'S PLAY!")

            case self.DIFFICULTY:
                return _("difficulty")
            case self.MODE:
                return _("mode")
            case self.BACK:
                return _("Back")

            case self.BLUFF:
                return _("Bluff!")


class UnoKeyboard(CallbackData, prefix='uno'):
    action: UnoActions | UnoAdd | UnoColors
    value: int | str = None


def setup():
    builder = InlineKeyboardBuilder()

    for action in tuple(UnoActions)[:4]:
        builder.button(text=action.word, callback_data=UnoKeyboard(action=action))

    builder.adjust(2, 1)
    return builder.as_markup()


def settings(message: types.Message):
    builder = InlineKeyboardBuilder()
    change = _("Change")

    for action in tuple(UnoActions)[4:6]:
        builder.button(text=f'{change} {action.word}', callback_data=UnoKeyboard(action=action))

    for enum, name in enumerate(UnoAdd.get_names()):
        add = UnoAdd.extract(message, enum)
        builder.button(
            text=f'{add.switcher} {name.lower()}',
            callback_data=UnoKeyboard(action=add, value=enum)
        )

    builder.button(text=UnoActions.BACK.word, callback_data=UnoKeyboard(action=UnoActions.BACK))

    builder.adjust(1)
    return builder.as_markup()


def show_cards(bluff: bool):
    builder = InlineKeyboardBuilder()

    if bluff:
        builder.button(text=UnoActions.BLUFF.word, callback_data=UnoKeyboard(action=UnoActions.BLUFF))

    builder.button(text=_("Show cards"), switch_inline_query_current_chat="uno")

    builder.adjust(1)
    return builder.as_markup()


def choice_color():
    builder = InlineKeyboardBuilder()

    for color in UnoColors.get_colors(exclude={UnoColors.black}):
        builder.button(text=color.word, callback_data=UnoKeyboard(action=color))

    builder.adjust(1)
    return builder.as_markup()


def say_uno():
    builder = InlineKeyboardBuilder()

    from .bot import UNO
    builder.button(text=UNO, callback_data=UnoKeyboard(action=UnoActions.UNO))

    return builder.as_markup()
