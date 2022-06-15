import asyncio
from typing import Any, Union, Optional

from aiogram import Bot
from aiogram.dispatcher.fsm.context import FSMContext
from aiogram.dispatcher.fsm.storage.base import BaseStorage, StorageKey
from asyncpg import Pool


class DataBaseContext:
    def __init__(self, bot: Bot, dp_pool: Pool, storage: BaseStorage, key: StorageKey):
        self.bot = bot
        self.storage = storage
        self.key = key

        self.dp_pool = dp_pool

    async def get_data(self, key: str) -> Any:
        data = (await self.storage.get_data(bot=self.bot, key=self.key)).get(key)

        if data == 'NULL':
            data = None
        elif not data:
            async with self.dp_pool.acquire() as conn:
                data = await conn.fetchval(f"""SELECT {key} FROM data WHERE ids = $1;""", self.key.chat_id) or \
                       await conn.fetchval(f"""SELECT {key} FROM data WHERE ids = 0;""")

                await self.storage.update_data(bot=self.bot, key=self.key, data={key: data or 'NULL'})
                timer(self, storage=key)

        return data

    async def set_data(self, data: Optional[dict] = None, **kwargs: Any) -> None:
        if data:
            kwargs.update(data)

        async with self.dp_pool.acquire() as conn:
            for key, data in kwargs.items():
                await conn.execute(
                    f"INSERT INTO data (ids, {key}) VALUES ($1, $2) ON CONFLICT (ids) DO UPDATE SET {key} = $2;",
                    self.key.chat_id, data
                )

        await self.storage.update_data(bot=self.bot, key=self.key, data=kwargs)
        timer(self, storage=key)

    async def update_data(self, data: Optional[dict] = None, **kwargs: Any) -> None:
        if data:
            kwargs.update(data)

        async with self.dp_pool.acquire() as conn:
            for key, data in kwargs.items():
                await conn.execute(f"UPDATE data SET {key} = $2 WHERE ids = $1;", self.key.chat_id, data)

        await self.storage.update_data(bot=self.bot, key=self.key, data=kwargs)
        timer(self, storage=key)

    async def clear(self) -> None:
        async with self.dp_pool.acquire() as conn:
            await conn.execute(f"DELETE FROM data WHERE ids = $1;", self.key.chat_id)

        await self.storage.set_data(bot=self.bot, key=self.key, data={})
        for task in asyncio.all_tasks():
            if f'storage:{self.key.chat_id}' in task.get_name():
                task.cancel()


def timer(
        self: Union[FSMContext, DataBaseContext],
        timeout: Optional[int] = 60 * 60 * 24 * 7,
        **kwargs: Any,
) -> asyncio.Task[Any]:
    async def waiter() -> Any:
        await asyncio.sleep(timeout)

        data = await self.storage.get_data(bot=self.bot, key=self.key)

        if data.pop(key, None):
            await self.storage.set_data(bot=self.bot, key=self.key, data=data)

        return data

    for group, key in kwargs.items():
        task_name = f'{group}:{self.key.chat_id}:{key}'

        for task in asyncio.all_tasks():
            if task.get_name() == task_name:
                task.cancel()
                break

        return asyncio.create_task(waiter(), name=task_name)


FSMContext.timer = timer
