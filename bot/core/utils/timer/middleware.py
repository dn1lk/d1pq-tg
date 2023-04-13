from typing import Callable, Any, Awaitable

from aiogram import Router, BaseMiddleware, types
from aiogram.dispatcher.flags import get_flag
from aiogram.fsm.context import FSMContext

from .tasks import TimerTasks


class TimerMiddleware(BaseMiddleware):
    async def __call__(
            self,
            handler: Callable[[types.TelegramObject, dict[str, Any]], Awaitable[Any]],
            event: types.TelegramObject,
            data: dict[str, Any],
    ):
        flag_timer: dict[str, str | bool] | None = get_flag(data, 'timer')

        if flag_timer:
            state: FSMContext = data['state']
            data['timer'] = timer = TimerTasks(flag_timer['name'])

            if flag_timer.get('cancelled', True):
                async with timer.lock(state.key):
                    return await handler(event, data)

        return await handler(event, data)

    def setup(self, router: Router):
        for observer in router.message, router.callback_query, router.chat_member:
            observer.middleware(self)
