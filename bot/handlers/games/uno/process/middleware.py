from typing import Dict, Any, Callable, Awaitable, Optional

from aiogram import BaseMiddleware
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.base import StorageKey
from aiogram.types import TelegramObject
from aiogram.utils.i18n import I18n

from .data import UnoData


class UnoFSMContextMiddleware(BaseMiddleware):
    async def __call__(
            self,
            handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
            event: TelegramObject,
            data: Dict[str, Any],
    ) -> Any:
        state: Optional[FSMContext] = data.get('state')

        if state:
            chat_id = (await state.get_data()).get('uno_room_id')

            if chat_id:
                state.key = StorageKey(
                    bot_id=state.key.bot_id,
                    chat_id=chat_id,
                    user_id=chat_id,
                    destiny=state.key.destiny,
                )

                data.update(
                    {
                        'event_chat': chat_id,
                        'state': state,
                        'raw_state': await state.get_state(),
                    }
                )

        return await handler(event, data)


class UnoDataMiddleware(BaseMiddleware):
    async def __call__(
            self,
            handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
            event: TelegramObject,
            data: Dict[str, Any],
    ) -> Any:
        state: Optional[FSMContext] = data.get('state')

        if state:
            data['data_uno']: UnoData = await UnoData.get(state)

        return await handler(event, data)
