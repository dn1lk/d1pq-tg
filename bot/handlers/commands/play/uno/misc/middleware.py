from collections.abc import Awaitable, Callable
from dataclasses import replace
from typing import TYPE_CHECKING, Any

from aiogram import Router
from aiogram.fsm.context import FSMContext
from aiogram.types import TelegramObject

from utils.database.middlewares import SQLGetMainMiddleware

from .data.players import UnoPlayerData

if TYPE_CHECKING:
    from aiogram.utils.i18n import I18nMiddleware


class UnoMiddleware(SQLGetMainMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        state: FSMContext = data["state"]

        key = UnoPlayerData.get_key(state.key.bot_id, state.key.user_id)
        data_state = await state.storage.get_data(key=key)
        if data_state:
            chat_id = data_state["0"]
            new_state = FSMContext(state.storage, replace(state.key, chat_id=chat_id, user_id=chat_id))

            new_data = data.copy()
            new_data.update(event_chat=chat_id, state=new_state, raw_state=await new_state.get_state())

            await self.update_data(new_data, chat_id, "main_settings")

            i18n_middleware: I18nMiddleware = new_data["i18n_middleware"]
            return await i18n_middleware(handler, event, new_data)

        return await handler(event, data)

    def setup(self, router: Router) -> None:
        router.inline_query.middleware(self)
