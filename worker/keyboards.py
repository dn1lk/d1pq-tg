from typing import Union, Optional, Any

from aiogram.dispatcher.filters.callback_data import CallbackData
from aiogram.utils.i18n import I18n, gettext as _, lazy_gettext as __
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder


class SettingsData(CallbackData, prefix='set'):
    name: str
    value: Any = None


BACK = __("Back")


def settings():
    datas = (
        ('commands', _('Add command')),
        ('locale', _('Change language')),
        ('chance', _('Change generation chance')),
        ('accuracy', _('Change generation accuracy')),
        ('data', _('Change data policy')),
    )

    builder = InlineKeyboardBuilder()

    for name, text in datas:
        builder.button(text=text, callback_data=SettingsData(name=name))

    builder.adjust(1)

    return builder.as_markup()


def get_locale_var(locales: tuple) -> zip:
    return zip(locales, ('English', 'Русский'))


def locale(i18n: I18n):
    builder = InlineKeyboardBuilder()

    for code, language in get_locale_var(i18n.available_locales):
        if code != i18n.current_locale:
            builder.button(text=language, callback_data=SettingsData(name='locale', value=code))

    builder.button(text=str(BACK), callback_data=SettingsData(name='back'))

    builder.adjust(1)

    return builder.as_markup()


def chance(markov_chance: Union[int, float]):
    datas = []

    for i in (6, 10):
        math = round(markov_chance / i, 2)

        if markov_chance > 10:
            datas.append(('-' + str(math), -math))

        if markov_chance < 90:
            datas.append(('+' + str(math), math))

    builder = InlineKeyboardBuilder()

    for text, value in datas:
        builder.button(
            text=text,
            callback_data=SettingsData(name='chance', value=value)
        )

    builder.button(text=str(BACK), callback_data=SettingsData(name='back'))

    builder.adjust(2)

    return builder.as_markup()


def accuracy(markov_state: int):
    builder = InlineKeyboardBuilder()

    for i in range(1, 5):
        if i != markov_state:
            builder.button(text=str(i), callback_data=SettingsData(name='accuracy', value=i))

    builder.button(text=str(BACK), callback_data=SettingsData(name='back'))

    builder.adjust(3, 1)

    return builder.as_markup()


def data(chat_type: str, members: Optional[dict] = None, messages: Optional[list] = None):
    datas = (
        ('messages', _('messages'), not messages or 'DECLINE' == messages),
        ('members', _('members'), bool(members)),
    )[slice(1 if chat_type == 'private' else 2)]

    builder = InlineKeyboardBuilder()

    for value, item, req in datas:
        builder.button(
            text=_('{req} recording {item}').format(req=_('Decline') if req else _('Allow'), item=item),
            callback_data=SettingsData(name='data', value=f'{value}-{"no" if req else "yes"}')
        )

    builder.button(
        text=_('Delete all data'),
        callback_data=SettingsData(name='data', value='delete')
    )
    builder.button(text=str(BACK), callback_data=SettingsData(name='back'))

    builder.adjust(1)

    return builder.as_markup()


def get_game_rps_args() -> dict:
    return {
        ("🪨", _("Rock")): _("Scissors").lower(),
        ("✂", _("Scissors")): _("Paper").lower(),
        ("📜", _("Paper")): _("Rock").lower(),
    }


def game_rps():
    builder = ReplyKeyboardBuilder()

    for item in get_game_rps_args().keys():
        builder.button(text=' '.join(item))

    builder.adjust(1)

    return builder.as_markup(resize_keyboard=True)
