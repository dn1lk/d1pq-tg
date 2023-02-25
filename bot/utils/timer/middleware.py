from typing import Callable, Any, Awaitable

from aiogram import Router, BaseMiddleware, types
from aiogram.dispatcher.flags import get_flag

from bot.middlewares import get_key
from . import tasks


class TimerMiddleware(BaseMiddleware):
    async def __call__(
            self,
            handler: Callable[[types.TelegramObject, dict[str, Any]], Awaitable[Any]],
            event: types.TelegramObject,
            data: dict[str, Any],
    ):
        timer: str | None = get_flag(data, 'timer')

        if timer:
            data['timer_key'] = key = get_key(data, timer)

            async with tasks.lock(key):
                return await handler(event, data)
        return await handler(event, data)

    def setup(self, router: Router):
        for observer in router.message, router.callback_query, router.chat_member:
            observer.middleware(self)
