import asyncio
from collections import defaultdict
from contextlib import asynccontextmanager
from typing import Callable, Any, Awaitable

from aiogram import BaseMiddleware, types
from aiogram.dispatcher.flags import get_flag
from aiogram.fsm.storage.base import StorageKey

from .task import TimerTask


class TimerMiddleware(BaseMiddleware):
    __tasks: set[asyncio.Task] = set()
    __locks: dict[StorageKey, asyncio.Lock] = defaultdict(asyncio.Lock)

    def __setitem__(self, key: StorageKey, task: asyncio.Task):
        self.__tasks.add(task)
        task.set_name(key)
        task.add_done_callback(self.__tasks.discard)

    def __getitem__(self, key: StorageKey):
        for task in self.__tasks:
            if task.get_name() == key:
                yield task

    async def __call__(
            self,
            handler: Callable[[types.TelegramObject, dict[str, Any]], Awaitable[Any]],
            event: types.TelegramObject,
            data: dict[str, Any],
    ):
        timer: str | None = get_flag(data, 'timer')

        if timer:
            key = self.get_key(data, timer)

            async with self.lock(key):
                result = await handler(event, data)

                if isinstance(result, TimerTask):
                    self.create(key, result)
                    return
                return result
        return await handler(event, data)

    @staticmethod
    def get_key(data: dict[str, Any], timer: str) -> StorageKey:
        chat_id: int = data.get('event_chat', data['event_from_user']).id
        bot_id: int = data['bot'].id

        return StorageKey(
            user_id=chat_id,
            chat_id=chat_id,
            bot_id=bot_id,
            destiny=timer,
        )

    @asynccontextmanager
    async def lock(self, key: StorageKey):
        self.cancel(key)
        async with self.__locks[key]:
            yield

    def cancel(self, key: StorageKey):
        for task in self[key]:
            task.cancel()

    def create(self, key: StorageKey, timer: TimerTask):
        self[key] = asyncio.create_task(timer.task())
