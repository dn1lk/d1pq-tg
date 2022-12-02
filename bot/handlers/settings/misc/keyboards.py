from enum import Enum, auto

from aiogram.filters.callback_data import CallbackData
from aiogram.utils.i18n import gettext as _
from aiogram.utils.keyboard import InlineKeyboardBuilder

from ..record.misc.data import RecordData


class SettingsAction(Enum):
    def _generate_next_value_(name, *args):
        return name.lower()

    COMMAND = auto()
    LOCALE = auto()
    CHANCE = auto()
    ACCURACY = auto()
    RECORD = auto()

    BACK = auto()

    @property
    def word(self) -> str | None:
        match self:
            case self.COMMAND:
                return _('Add command')
            case self.LOCALE:
                return _('Change language')
            case self.CHANCE:
                return _('Change generation chance')
            case self.ACCURACY:
                return _('Change generation accuracy')
            case self.RECORD:
                return _('Change record policy')

            case self.BACK:
                return _("Back")


class SettingsKeyboard(CallbackData, prefix='set'):
    action: SettingsAction | RecordData
    value: int | float | str = None


def settings():
    builder = InlineKeyboardBuilder()

    for action in tuple(SettingsAction)[:5]:
        builder.button(text=action.word, callback_data=SettingsKeyboard(action=action))

    builder.adjust(1)
    return builder.as_markup()


def back(builder: InlineKeyboardBuilder):
    return builder.button(
        text=SettingsAction.BACK.word,
        callback_data=SettingsKeyboard(action=SettingsAction.BACK)
    )


def locale(locales: dict[str, str], current_locale: str):
    builder = InlineKeyboardBuilder()

    for code, language in locales.items():
        if code != current_locale:
            builder.button(
                text=language,
                callback_data=SettingsKeyboard(action=SettingsAction.LOCALE, value=code)
            )

    back(builder)
    builder.adjust(1)
    return builder.as_markup()


def chance(markov_chance: int | float):
    builder = InlineKeyboardBuilder()

    for i in 6, 10:
        math = round(markov_chance / i, 2)

        if markov_chance > 5:
            builder.button(
                text=f'-{math}',
                callback_data=SettingsKeyboard(action=SettingsAction.CHANCE, value=markov_chance - math)
            )

        if markov_chance < 90:
            builder.button(
                text=f'+{math}',
                callback_data=SettingsKeyboard(action=SettingsAction.CHANCE, value=markov_chance + math)
            )

    back(builder)
    builder.adjust(2)
    return builder.as_markup()


def accuracy(markov_state: int):
    builder = InlineKeyboardBuilder()

    for i in range(1, 5):
        if i != markov_state:
            builder.button(text=str(i), callback_data=SettingsKeyboard(action=SettingsAction.ACCURACY, value=i))

    back(builder)
    builder.adjust(3, 1)
    return builder.as_markup()


def record(buttons: dict[RecordData, int]):
    text = _('{action} {data} recording')
    builder = InlineKeyboardBuilder()

    for action, value in buttons.items():
        builder.button(
            text=text.format(action=_('Disable') if value else _('Enable'), data=action.word.lower()),
            callback_data=SettingsKeyboard(action=action, value=value)
        )

    builder.button(text=RecordData.DELETE.word, callback_data=SettingsKeyboard(action=RecordData.DELETE))

    back(builder)
    builder.adjust(1)
    return builder.as_markup()
