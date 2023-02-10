from .. import Settings
from ..keyboard import *


class LocaleKeyboard(CallbackData, prefix=Settings.LOCALE.value):
    value: str


def locale(locales: dict[str, str], current_locale: str):
    builder = InlineKeyboardBuilder()

    for code, language in locales.items():
        if code != current_locale:
            builder.button(text=language,
                           callback_data=SettingsKeyboard(value=code))

    back(builder)
    builder.adjust(1)
    return builder.as_markup()
