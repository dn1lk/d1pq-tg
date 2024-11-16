from collections.abc import Awaitable, Callable
from dataclasses import replace
from typing import Any

from aiogram import BaseMiddleware, Router, types
from aiogram.fsm.context import FSMContext


class DestinySetMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[types.TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: types.TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        state: FSMContext = data["state"]
        new_state = FSMContext(state.storage, replace(state.key, destiny=data["event_router"].name))

        new_data = data.copy()
        new_data.update(state=new_state, raw_state=await new_state.get_state())

        return await handler(event, new_data)

    def setup(self, router: Router) -> None:
        for observer in router.observers.values():
            observer.outer_middleware(self)
