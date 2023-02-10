from ..keyboard import *


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
