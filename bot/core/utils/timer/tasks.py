import asyncio
import logging
from collections import defaultdict
from contextlib import asynccontextmanager
from dataclasses import fields
from typing import Coroutine, AsyncGenerator, Generator

from aiogram.fsm.storage.base import StorageKey

logger = logging.getLogger('tasks')


class TimerTasks:
    _tasks: set[asyncio.Task] = set()
    _locks: dict[str, asyncio.Lock] = defaultdict(asyncio.Lock)

    def __setitem__(self, key: StorageKey, coro: Coroutine):
        key = self._get_key(key)

        task = asyncio.create_task(coro)
        self._tasks.add(task)

        task.set_name(key)
        task.add_done_callback(self._tasks.discard)
        task.add_done_callback(lambda _: logger.debug(f'Finished task: {task}'))

        logger.debug(f'Created task: {task}')

    def __getitem__(self, key: StorageKey) -> Generator[asyncio.Task, None, None]:
        key = self._get_key(key)

        for task in self._tasks:
            if task.get_name() == key:
                yield task

    def __delitem__(self, key: StorageKey):
        for task in self[key]:
            if task is not asyncio.current_task():
                task.cancel()

                logger.debug(f'Canceled task: {task}')

    def update(self, key: StorageKey, coro: Coroutine):
        """ Stop existed coro by key and add new """

        del self[key]
        self[key] = coro

    @staticmethod
    def _get_key(key: StorageKey) -> str:
        return ':'.join(str(getattr(key, field.name)) for field in fields(key))

    @asynccontextmanager
    async def lock(self, key: StorageKey) -> AsyncGenerator[None, None]:
        key = self._get_key(key)

        async with self._locks[key]:
            yield
