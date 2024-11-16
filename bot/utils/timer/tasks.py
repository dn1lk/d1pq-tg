import asyncio
import logging
from collections import defaultdict
from collections.abc import AsyncGenerator, Coroutine, Generator
from contextlib import asynccontextmanager
from dataclasses import fields
from typing import ClassVar

from aiogram.fsm.storage.base import StorageKey

logger = logging.getLogger("bot.tasks")


class TimerTasks:
    _tasks: ClassVar[set[asyncio.Task]] = set()
    _locks: ClassVar[dict[str, asyncio.Lock]] = defaultdict(asyncio.Lock)

    def __setitem__(self, key: StorageKey, coro: Coroutine) -> None:
        task_name = self._get_key(key)

        task = asyncio.create_task(coro)
        self._tasks.add(task)

        task.set_name(task_name)
        task.add_done_callback(self._tasks.discard)
        task.add_done_callback(lambda _: logger.debug("task finished: %s", key))

        logger.debug("task created: %s", key)

    def __getitem__(self, key: StorageKey) -> Generator[asyncio.Task, None, None]:
        task_name = self._get_key(key)

        for task in self._tasks:
            if task.get_name() == task_name:
                yield task

    def __delitem__(self, key: StorageKey) -> None:
        for task in self[key]:
            if task is not asyncio.current_task():
                task.cancel()

                logger.debug("task canceled: %s", key)

    def update(self, key: StorageKey, coro: Coroutine) -> None:
        """Stop existed coro by key and add new"""

        del self[key]
        self[key] = coro

    @staticmethod
    def _get_key(key: StorageKey) -> str:
        return ":".join(str(getattr(key, field.name)) for field in fields(key))

    @asynccontextmanager
    async def lock(self, key: StorageKey) -> AsyncGenerator[None, None]:
        task_name = self._get_key(key)

        async with self._locks[task_name]:
            logger.debug("lock acquired: %s", key)
            yield

        logger.debug("lock released: %s", key)

    @classmethod
    def close(cls) -> None:
        for task in cls._tasks:
            task.cancel()
