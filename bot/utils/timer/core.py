import asyncio
from typing import Coroutine

from aiogram.fsm.context import FSMContext


class Timer:
    tasks: dict[str, asyncio.Task] = {}

    def __setitem__(self, name: str, task: asyncio.Task):
        self.tasks[name] = task

        task.set_name(name)
        task.add_done_callback(lambda _: self.tasks.pop(name, None))

    def __getitem__(self, name: str):
        return self.tasks.get(name)

    @staticmethod
    def dict(coro: Coroutine = None, coro_done: Coroutine = None) -> dict[str, Coroutine]:
        return {'coro': coro, 'coro_done': coro_done}

    @staticmethod
    def get_name(state: FSMContext, name: str):
        return f'{state.key.chat_id}:{name}'

    def create(
            self,
            name: str,
            delay: int = 60,
            coro: Coroutine = None,
            coro_done: Coroutine = None,
    ) -> asyncio.Task:
        async def waiter():
            if delay:
                await asyncio.sleep(delay=delay)
            if coro:
                await coro

        task = asyncio.create_task(waiter())

        if coro_done:
            task.add_done_callback(lambda _: asyncio.create_task(coro_done))

        self[name] = task
        return task

    async def cancel(self, name: str) -> asyncio.Task | None:
        task = self[name]

        if task and task is not asyncio.current_task():
            task.cancel()

            try:
                await task
            except asyncio.CancelledError:
                pass

            return task
