from typing import Dict, Any, Callable, Awaitable, Optional, Union

from aiogram import BaseMiddleware
from aiogram.dispatcher.flags import get_flag
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.base import StorageKey
from aiogram.types import TelegramObject

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
            chat_id = (await state.get_data()).get('uno_chat_id')

            if chat_id:
                state.key = StorageKey(
                    bot_id=state.key.bot_id,
                    chat_id=chat_id,
                    user_id=chat_id,
                    destiny=state.key.destiny,
                )

                data.update(
                    {
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
        flag_data: Optional[Union[str, set]] = get_flag(data, 'uno')

        if flag_data:
            state: Optional[FSMContext] = data.get('state')

            if state:
                data_uno = (await state.get_data()).get('uno')
                data['data_uno'] = UnoData(**data_uno) if data_uno else None

        return await handler(event, data)
