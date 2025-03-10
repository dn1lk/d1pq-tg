from collections.abc import Awaitable, Callable
from dataclasses import replace
from typing import TYPE_CHECKING, Any

from aiogram import BaseMiddleware, Router, types
from aiogram.dispatcher.flags import get_flag

if TYPE_CHECKING:
    from aiogram.fsm.context import FSMContext

    from . import TimerTasks


class TimerMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[types.TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: types.TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        flag_timer: dict[str, str | bool] | str | None = get_flag(data, "timer")

        if flag_timer:
            match flag_timer:
                case str():
                    flag_timer = {"name": flag_timer}
                case bool():
                    flag_timer = {}

            timer: TimerTasks = data["timer"]
            state: FSMContext = data["state"]

            key = replace(state.key, destiny=flag_timer["name"]) if "name" in flag_timer else state.key

            if flag_timer.get("cancelled", True):
                del timer[key]

            if flag_timer.get("locked", True):
                async with timer.lock(key):
                    return await handler(event, data)

        return await handler(event, data)

    def setup(self, router: Router) -> None:
        for observer in router.message, router.callback_query, router.chat_member:
            observer.middleware(self)
