import asyncio

from aiogram.fsm.context import FSMContext


class Timer:
    tasks: dict[str, asyncio.Task] = {}

    def __setitem__(self, name: str, task: asyncio.Task):
        def del_task(t: asyncio.Task):
            if t is self[name]:
                del self.tasks[name]

        self.tasks[name] = task
        task.set_name(name)
        task.add_done_callback(del_task)

    def __getitem__(self, name):
        return self.tasks.get(name)

    def __delitem__(self, name):
        self.tasks[name].cancel()

    @staticmethod
    def get_name(state, name: str):
        return f'{state.key.chat_id}:{name}'

    def create(
            self,
            state: FSMContext,
            coroutine=None,
            coroutine_done=None,
            name: str = 'default',
            delay: int = 60,
            **kwargs
    ) -> asyncio.Task:
        async def waiter():
            try:
                await asyncio.sleep(delay=delay)

                if coroutine:
                    await coroutine(state=state, **kwargs)
            finally:
                if coroutine_done:
                    await coroutine_done(state=state, **kwargs)

        task = asyncio.create_task(coro=waiter())
        self[self.get_name(state, name)] = task

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


timer = Timer()
