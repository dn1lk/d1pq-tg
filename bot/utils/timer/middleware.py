from typing import Callable, Dict, Any, Awaitable

from aiogram import BaseMiddleware, types
from aiogram.dispatcher.flags import get_flag

from . import timer


class TimerMiddleware(BaseMiddleware):
    async def __call__(
            self,
            handler: Callable[[types.TelegramObject, Dict[str, Any]], Awaitable[Any]],
            event: types.TelegramObject,
            data: Dict[str, Any],
    ) -> Any:
        flag_data = get_flag(data, 'timer')

        if flag_data:
            if isinstance(flag_data, tuple):
                name, delay = flag_data
            else:
                name, delay = flag_data, 60

            task_name = timer.get_name(data['state'], name)
            await timer.cancel(task_name)

            coroutines = await handler(event, data)

            if coroutines:
                timer.create(task_name, delay, **coroutines)

            return coroutines
        return await handler(event, data)
