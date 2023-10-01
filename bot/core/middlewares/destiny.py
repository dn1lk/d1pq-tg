from dataclasses import replace
from typing import Callable, Any, Awaitable

from aiogram import Router, BaseMiddleware, types
from aiogram.dispatcher.event.bases import UNHANDLED
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.base import StorageKey


class DestinySetMiddleware(BaseMiddleware):
    async def __call__(
            self,
            handler: Callable[[types.Update, dict[str, Any]], Awaitable[Any]],
            event: types.Update,
            data: dict[str, Any]
    ):
        state: FSMContext = data['state']

        key_old = state.key
        key_new = replace(state.key, destiny=data['event_router'].name)

        await self.update_key(data, state, key_new)

        result = await handler(event, data)

        if result is UNHANDLED:
            await self.update_key(data, state, key_old)

        return result

    @staticmethod
    async def update_key(data: dict[str, Any], state: FSMContext, key: StorageKey):
        state.key = key
        data.update(raw_state=await state.get_state())

    def setup(self, router: Router):
        for observer in router.observers.values():
            observer.outer_middleware(self)
