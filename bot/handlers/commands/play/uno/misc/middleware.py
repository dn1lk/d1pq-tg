from dataclasses import replace
from typing import Dict, Any, Callable, Awaitable

from aiogram import Router
from aiogram.fsm.context import FSMContext
from aiogram.types import TelegramObject
from aiogram.utils.i18n import I18nMiddleware

from core.utils.database.middleware import SQLGetMainMiddleware
from .data.players import UnoPlayerData


class UnoMiddleware(SQLGetMainMiddleware):
    async def __call__(
            self,
            handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
            event: TelegramObject,
            data: Dict[str, Any],
    ):
        state: FSMContext = data["state"]

        data_state = await state.storage.get_data(
            key=UnoPlayerData.get_key(state.key.bot_id, state.key.user_id)
        )

        if data_state:
            chat_id = data['event_chat'] = data_state['0']
            state.key = replace(state.key, chat_id=chat_id, user_id=chat_id)

            await self.update_data(data, chat_id)

            i18n_middleware: I18nMiddleware = data["i18n_middleware"]
            return await i18n_middleware(handler, event, data)
        return await handler(event, data)

    def setup(self, router: Router):
        router.inline_query.middleware(self)
