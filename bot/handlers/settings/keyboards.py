from functools import lru_cache

from aiogram.filters.callback_data import CallbackData
from aiogram.utils.i18n import gettext as _, I18n
from aiogram.utils.keyboard import InlineKeyboardBuilder


class Settings(CallbackData, prefix='set'):
    name: str
    value: bool | int | str | None


def settings():
    buttons = {
        'commands': _('Add command'),
        'locale': _('Change language'),
        'chance': _('Change generation chance'),
        'accuracy': _('Change generation accuracy'),
        'data': _('Change data policy'),
    }

    builder = InlineKeyboardBuilder()

    for name, text in buttons.items():
        builder.button(text=text, callback_data=Settings(name=name))

    builder.adjust(1)
    return builder.as_markup()


def settings_back(builder: InlineKeyboardBuilder):
    return builder.button(text=_("Back"), callback_data=Settings(name='back'))


@lru_cache(maxsize=1)
def get_locale_vars(locales: tuple) -> zip:
    print(locales)
    return zip(locales, ('English', 'Русский'))


def locale(i18n: I18n):
    builder = InlineKeyboardBuilder()

    for code, language in get_locale_vars(i18n.available_locales):
        if code != i18n.current_locale:
            builder.button(text=language, callback_data=Settings(name='locale', value=code))

    settings_back(builder)
    builder.adjust(1)
    return builder.as_markup()


def chance(markov_chance: int | float):
    builder = InlineKeyboardBuilder()

    for i in 6, 10:
        math = round(markov_chance / i, 2)

        if markov_chance > 10:
            builder.button(text=f'-{math}', callback_data=Settings(name='chance', value=markov_chance - math))

        if markov_chance < 90:
            builder.button(text=f'+{math}', callback_data=Settings(name='chance', value=markov_chance + math))

    settings_back(builder)
    builder.adjust(2)
    return builder.as_markup()


def accuracy(markov_state: int):
    builder = InlineKeyboardBuilder()

    for i in range(1, 5):
        if i != markov_state:
            builder.button(text=str(i), callback_data=Settings(name='accuracy', value=i))

    settings_back(builder)
    builder.adjust(3, 1)
    return builder.as_markup()


def data(**buttons):
    text = _('{action} {item} recording')
    builder = InlineKeyboardBuilder()

    for key, value in buttons.items():
        builder.button(
            text=text.format(action=_('Enable') if value[1] else _('Disable'), item=key.lower()),
            callback_data=Settings(name=key, value=value[1])
        )

    builder.button(text=_('Delete all data'), callback_data=Settings(name='delete'))

    settings_back(builder)
    builder.adjust(1)
    return builder.as_markup()
