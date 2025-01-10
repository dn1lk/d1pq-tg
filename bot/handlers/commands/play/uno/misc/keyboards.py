from enum import Enum

from aiogram import types
from aiogram.filters.callback_data import CallbackData
from aiogram.utils.i18n import gettext as _
from aiogram.utils.keyboard import InlineKeyboardBuilder

from handlers.commands.play import PlayActions
from handlers.commands.play.uno import UNO

from .data.deck.colors import UnoColors
from .data.settings.additions import UnoAdd, UnoAddState


class UnoSetup(str, Enum):
    JOIN = "join"
    LEAVE = "leave"
    SETTINGS = "settings"
    START = "start"

    def __str__(self) -> str:
        match self:
            case self.JOIN:
                setup = _("Yes")
            case self.LEAVE:
                setup = _("No")
            case self.SETTINGS:
                setup = _("Settings")
            case self.START:
                setup = _("LET'S PLAY!")
            case _:
                msg = f"{self.__class__.__name__}: unexpected value: {self}"
                raise TypeError(msg)

        return setup


class UnoSettings(str, Enum):
    DIFFICULTY = "difficulty"
    MODE = "mode"

    def __str__(self) -> str:
        match self:
            case self.DIFFICULTY:
                settings = _("difficulty")
            case self.MODE:
                settings = _("mode")
            case _:
                msg = f"{self.__class__.__name__}: unexpected value: {self}"
                raise TypeError(msg)

        return settings


class UnoActions(str, Enum):
    BLUFF = "bluff"
    COLOR = "color"
    UNO = "uno"

    BACK = "back"

    def __str__(self) -> str:
        match self:
            case self.BACK:
                action = _("Back")
            case _:
                msg = f"{self.__class__.__name__}: unexpected value: {self}"
                raise TypeError(msg)

        return action


class UnoData(CallbackData, prefix=PlayActions.UNO[0]):
    action: UnoActions | UnoSetup | UnoSettings | UnoAdd
    value: UnoAddState | UnoColors | None = None


def setup_keyboard() -> types.InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    for action in UnoSetup:
        builder.button(text=str(action), callback_data=UnoData(action=action))

    builder.adjust(2, 1)
    return builder.as_markup()


def settings_keyboard(message: types.Message) -> types.InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    for action in UnoSettings:
        builder.button(
            text=_("Change {settings}").format(settings=str(action)),
            callback_data=UnoData(action=action),
        )

    for add in UnoAdd:
        add_state = add.extract(message)
        builder.button(
            text=f"{add_state.button} {str(add).lower()}",
            callback_data=UnoData(action=add, value=add_state),
        )

    builder.button(
        text=str(UnoActions.BACK),
        callback_data=UnoData(action=UnoActions.BACK),
    )

    builder.adjust(1)
    return builder.as_markup()


def show_cards(*, bluffed: bool) -> types.InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    if bluffed:
        builder.button(text=_("Bluff!"), callback_data=UnoData(action=UnoActions.BLUFF))

    builder.button(text=_("Show cards"), switch_inline_query_current_chat="uno")

    builder.adjust(1)
    return builder.as_markup()


def choice_color() -> types.InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    for color in UnoColors.exclude(UnoColors.BLACK):
        builder.button(text=str(color), callback_data=UnoData(action=UnoActions.COLOR, value=color))

    builder.adjust(1)
    return builder.as_markup()


def say_uno() -> types.InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    builder.button(text=UNO, callback_data=UnoData(action=UnoActions.UNO))

    return builder.as_markup()
