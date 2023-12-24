from aiogram.filters.callback_data import CallbackData
from aiogram.utils.keyboard import InlineKeyboardBuilder

from handlers.commands.misc.types import CommandTypes
from .actions import GPTOptionsActions
from ...misc.keyboards import add_back_button


class GPTOptionsData(CallbackData, prefix=f'{CommandTypes.SETTINGS[0]}_gpt'):
    action: GPTOptionsActions
    value: int | None = None


def add_gpt_back_button(builder: InlineKeyboardBuilder):
    return builder.button(
        text=GPTOptionsActions.BACK.keyboard,
        callback_data=GPTOptionsData(action=GPTOptionsActions.BACK)
    )


def actions_keyboard(actions: set):
    builder = InlineKeyboardBuilder()

    for action in actions:
        builder.button(text=action.keyboard, callback_data=GPTOptionsData(action=action))

    add_back_button(builder)

    builder.adjust(1)
    return builder.as_markup()


def temperature_keyboard(current_temperature: float):
    current_temperature = int(round(current_temperature, 2) * 10)

    builder = InlineKeyboardBuilder()

    for temperature in range(1, 11):
        if temperature != current_temperature:
            builder.button(
                text=f'{round(temperature / 10, 2)}',
                callback_data=GPTOptionsData(action=GPTOptionsActions.TEMPERATURE, value=temperature)
            )

    add_gpt_back_button(builder)

    builder.adjust(3)
    return builder.as_markup()
