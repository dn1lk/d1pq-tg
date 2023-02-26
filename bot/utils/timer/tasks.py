import asyncio
from collections import defaultdict
from contextlib import asynccontextmanager
from typing import Coroutine

from aiogram.fsm.storage.base import StorageKey


class Tasks:
    __tasks: set[asyncio.Task] = set()
    __locks: dict[StorageKey, asyncio.Lock] = defaultdict(asyncio.Lock)

    def __setitem__(self, key: StorageKey, coro: Coroutine):
        task = asyncio.create_task(coro)

        self.__tasks.add(task)
        task.set_name(key)
        task.add_done_callback(self.__tasks.discard)

    def __getitem__(self, key: StorageKey):
        key = str(key)

        for task in self.__tasks:
            if task.get_name() == key:
                yield task

    def __delitem__(self, key: StorageKey):
        for task in self[key]:
            task.cancel()

    @asynccontextmanager
    async def lock(self, key: StorageKey):
        del self[key]

        async with self.__locks[key]:
            yield
