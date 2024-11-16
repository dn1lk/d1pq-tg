from typing import Literal

from aiogram import Bot, types
from aiogram.fsm.context import FSMContext
from aiogram.utils.chat_action import ChatActionSender
from aiogram.utils.i18n import I18n
from Levenshtein import ratio

from core.filters import BaseFilter

from .data import CTSData

EXCEPTION_LETTERS = "ь", "ъ"
CITY_RATIO = 0.85


class CTSFilter(BaseFilter):
    async def __call__(self, message: types.Message, bot: Bot, state: FSMContext, i18n: I18n) -> dict | Literal[False]:
        data = await CTSData.get_data(state)
        if data is None:
            return False

        bot_city = data.bot_city
        user_city = message.text
        assert user_city is not None, "wrong user city"

        async with ChatActionSender.typing(chat_id=message.chat.id, bot=bot):
            if bot_city is None:
                return self.check_city(i18n, data, user_city)

            if user_city[0].lower() == bot_city[-1].lower():
                return self.check_city(i18n, data, user_city)

            if user_city[0].lower() == bot_city[-2].lower() and bot_city[-1].lower() in EXCEPTION_LETTERS:
                return self.check_city(i18n, data, user_city)

        return False

    @staticmethod
    def check_city(i18n: I18n, data: CTSData, user_city: str) -> dict | Literal[False]:
        if user_city not in data.used_cities:
            cities = data.get_cities(i18n.current_locale)

            if any(ratio(city, user_city) > CITY_RATIO for city in cities if city[0].lower() == user_city[0].lower()):
                data.used_cities.append(user_city)
                data.gen_city(cities, user_city)

                return {"data_cts": data}

        return False
