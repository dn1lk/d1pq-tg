from typing import Dict, Any, Callable, Awaitable, Optional

from aiogram import BaseMiddleware
from aiogram.dispatcher.fsm.context import FSMContext
from aiogram.dispatcher.fsm.storage.base import StorageKey
from aiogram.types import TelegramObject


class UnoFSMContextMiddleware(BaseMiddleware):
    async def __call__(
            self,
            handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
            event: TelegramObject,
            data: Dict[str, Any],
    ) -> Any:
        state: Optional[FSMContext] = data.get('state')

        if state:
            uno_chat_id = (await state.get_data()).get('uno_chat_id')

            if uno_chat_id:
                state.key = StorageKey(
                    bot_id=state.key.bot_id,
                    chat_id=uno_chat_id,
                    user_id=uno_chat_id,
                    destiny=state.key.destiny,
                )

                data.update(
                    {
                        'state': state,
                        'raw_state': await state.get_state(),
                    }
                )

        return await handler(event, data)
