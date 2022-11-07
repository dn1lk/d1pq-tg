from aiogram.filters.callback_data import CallbackData
from aiogram.utils.i18n import gettext as _
from aiogram.utils.keyboard import InlineKeyboardBuilder


class SettingsKeyboard(CallbackData, prefix='set'):
    action: str
    value: int | str | None


def settings():
    buttons = {
        'commands': _('Add command'),
        'locale': _('Change language'),
        'chance': _('Change generation chance'),
        'accuracy': _('Change generation accuracy'),
        'record': _('Change record policy'),
    }

    builder = InlineKeyboardBuilder()

    for action, text in buttons.items():
        builder.button(text=text, callback_data=SettingsKeyboard(action=action))

    builder.adjust(1)
    return builder.as_markup()


def settings_back(builder: InlineKeyboardBuilder):
    return builder.button(text=_("Back"), callback_data=SettingsKeyboard(action='back'))


def locale(locales: tuple[tuple[str, str], ...], current_locale: str):
    builder = InlineKeyboardBuilder()

    for code, language in locales:
        if code != current_locale:
            builder.button(text=language, callback_data=SettingsKeyboard(action='locale', value=code))

    settings_back(builder)
    builder.adjust(1)
    return builder.as_markup()


def chance(markov_chance: int | float):
    builder = InlineKeyboardBuilder()

    for i in 6, 10:
        math = round(markov_chance / i, 2)

        if markov_chance > 10:
            builder.button(text=f'-{math}', callback_data=SettingsKeyboard(action='chance', value=markov_chance - math))

        if markov_chance < 90:
            builder.button(text=f'+{math}', callback_data=SettingsKeyboard(action='chance', value=markov_chance + math))

    settings_back(builder)
    builder.adjust(2)
    return builder.as_markup()


def accuracy(markov_state: int):
    builder = InlineKeyboardBuilder()

    for i in range(1, 5):
        if i != markov_state:
            builder.button(text=str(i), callback_data=SettingsKeyboard(action='accuracy', value=i))

    settings_back(builder)
    builder.adjust(3, 1)
    return builder.as_markup()


def data(buttons: dict):
    text = _('{action} {data} recording')
    builder = InlineKeyboardBuilder()

    for action, value in buttons.items():
        builder.button(
            text=text.format(action=_('Disable') if value else _('Enable'), data=action.word.lower()),
            callback_data=SettingsKeyboard(action=action.name, value=value)
        )

    builder.button(text=_('Delete all records'), callback_data=SettingsKeyboard(action='delete'))

    settings_back(builder)
    builder.adjust(1)
    return builder.as_markup()
