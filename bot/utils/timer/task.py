import asyncio
import types


class TimerTask:
    def __init__(self, *coroutines: types.CoroutineType, coroutine_done: types.CoroutineType, delay: int = 60):
        self.coroutines = coroutines
        self.coroutine_done = coroutine_done
        self.delay = delay

    def __iter__(self):
        for coroutine in self.coroutines:
            yield coroutine

    async def task(self):
        try:
            await asyncio.sleep(self.delay)
            for coroutine in self.coroutines:
                await coroutine
        finally:
            await self.coroutine_done
