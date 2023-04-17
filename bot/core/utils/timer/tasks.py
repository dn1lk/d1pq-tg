import asyncio
from collections import defaultdict
from contextlib import asynccontextmanager
from typing import Coroutine, AsyncGenerator

from aiogram.fsm.storage.base import StorageKey


class TimerTasks:
    _tasks: set[asyncio.Task] = set()
    _locks: dict[str, asyncio.Lock] = defaultdict(asyncio.Lock)

    __slots__ = {"destiny"}

    def __init__(self, destiny: str):
        self.destiny = destiny

    def __setitem__(self, key: StorageKey, coro: Coroutine):
        key = self.get_key(key)
        task = asyncio.create_task(coro)

        self._tasks.add(task)
        task.set_name(key)
        task.add_done_callback(self._tasks.discard)

    def __getitem__(self, key: StorageKey):
        key = self.get_key(key)

        for task in self._tasks:
            if task.get_name() == key:
                yield task

    def __delitem__(self, key: StorageKey):
        for task in self[key]:
            if task is not asyncio.current_task():
                task.cancel()

    def get_key(self, key: StorageKey) -> str:
        return f'{key.bot_id}:{key.chat_id}:{key.user_id}:{self.destiny}'

    @asynccontextmanager
    async def lock(self, key: StorageKey) -> AsyncGenerator[None, None]:
        async with self._locks[self.get_key(key)]:
            yield
