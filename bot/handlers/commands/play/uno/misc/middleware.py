from typing import Dict, Any, Callable, Awaitable

from aiogram import Router, BaseMiddleware
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.base import StorageKey
from aiogram.types import TelegramObject
from aiogram.utils.i18n import I18nMiddleware

from .data.players import UnoPlayer


class UnoMiddleware(BaseMiddleware):
    async def __call__(
            self,
            handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
            event: TelegramObject,
            data: Dict[str, Any],
    ):
        state: FSMContext = data["state"]
        data_state = await state.storage.get_data(
            bot=state.bot,
            key=UnoPlayer.get_key(state.key.bot_id, state.key.user_id)
        )

        if data_state:
            data["event_chat"] = chat = await state.bot.get_chat(data_state['0'])

            state.key = StorageKey(
                bot_id=state.key.bot_id,
                chat_id=chat.id,
                user_id=state.key.user_id,
                destiny=state.key.destiny,
            )
            data["state"] = state

            i18n_middleware: I18nMiddleware = data["i18n_middleware"]
            return await i18n_middleware(handler, event, data)
        return await handler(event, data)

    def setup(self, router: Router):
        router.inline_query.middleware(self)
