from dataclasses import replace
from typing import Callable, Any, Awaitable

from aiogram import Router, BaseMiddleware, types
from aiogram.dispatcher.flags import get_flag
from aiogram.fsm.context import FSMContext

from . import TimerTasks


class TimerMiddleware(BaseMiddleware):
    async def __call__(
            self,
            handler: Callable[[types.TelegramObject, dict[str, Any]], Awaitable[Any]],
            event: types.TelegramObject,
            data: dict[str, Any],
    ):
        flag_timer: dict[str, str | bool] | str | None = get_flag(data, 'timer')

        if flag_timer:
            if isinstance(flag_timer, str):
                flag_timer = {'name': flag_timer}
            elif isinstance(flag_timer, bool):
                flag_timer = {}

            timer: TimerTasks = data['timer']
            state: FSMContext = data['state']

            if 'name' in flag_timer:
                key = replace(state.key, destiny=flag_timer['name'])
            else:
                key = state.key

            if flag_timer.get('cancelled', True):
                del timer[key]

            if flag_timer.get('locked', True):
                async with timer.lock(key):
                    return await handler(event, data)

        return await handler(event, data)

    def setup(self, router: Router):
        for observer in router.message, router.callback_query, router.chat_member:
            observer.middleware(self)
