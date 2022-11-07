from aiogram import types
from aiogram.filters import Filter
from aiogram.fsm.context import FSMContext
from aiogram.utils.chat_action import ChatActionSender
from aiogram.utils.i18n import I18n

from bot import filters as f
from .data import CTSData, get_cities


class CTSFilter(Filter):
    async def __call__(self, message: types.Message, state: FSMContext, i18n: I18n, data_cts: CTSData) -> dict | None:
        def filter_user_var():
            for game_var in game_vars:
                if game_var[0].lower() == message.text[0].lower():
                    yield f.LevenshteinFilter.lev_distance(game_var, message.text) <= max(len(game_var) / 5, 1)

        async with ChatActionSender.typing(chat_id=message.chat.id):
            if not data_cts.bot_var or \
                    message.text[0].lower() == data_cts.bot_var[-1].lower() or \
                    message.text[0].lower() == data_cts.bot_var[-2].lower() and \
                    data_cts.bot_var[-1].lower() in ('ь', 'ъ'):
                if message.text not in data_cts.cities:
                    game_vars = get_cities(i18n.current_locale)

                    if any(filter_user_var()):
                        data_cts.cities.append(message.text)
                        data_cts.gen_var(message.text, game_vars)

                        return {'data_cts': data_cts}
