from typing import Dict, Any, Callable, Awaitable, Optional

from aiogram import BaseMiddleware
from aiogram.fsm.context import FSMContext
from aiogram.types import TelegramObject

from .data import CTSData


class CTSDataMiddleware(BaseMiddleware):
    async def __call__(
            self,
            handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
            event: TelegramObject,
            data: Dict[str, Any],
    ) -> Any:
        state: Optional[FSMContext] = data.get('state')

        if state:
            data['data_cts'] = await CTSData.get_data(state)

        return await handler(event, data)
