from typing import Any, Optional

from aiogram import Bot
from aiogram.fsm.storage.base import BaseStorage, StorageKey
from asyncpg import Pool


class DataBaseContext:
    def __init__(self, bot: Bot, storage: BaseStorage, key: StorageKey, pool_db: Pool):
        self.bot = bot
        self.storage = storage
        self.key = key

        self.pool_db = pool_db

    async def get_data(self, key: str) -> Any:
        data = (await self.storage.get_data(bot=self.bot, key=self.key)).get(key)

        if data == 'null':
            data = None
        elif not data:
            async with self.pool_db.acquire() as conn:
                data = await conn.fetchval(f"SELECT {key} FROM data WHERE id = $1;", self.key.chat_id) or \
                       await conn.fetchval(f"SELECT {key} FROM data WHERE id = 0;")

            await self.storage.update_data(bot=self.bot, key=self.key, data={key: data or 'null'})

        return data

    async def set_data(self, data: Optional[dict] = None, **kwargs: Any) -> None:
        if data:
            kwargs.update(data)

        async with self.pool_db.acquire() as conn:
            for key, data in kwargs.items():
                await conn.execute(
                    f"INSERT INTO data (id, {key}) VALUES ($1, $2) ON CONFLICT (id) DO UPDATE SET {key} = $2;",
                    self.key.chat_id, data
                )

        await self.storage.update_data(bot=self.bot, key=self.key, data=kwargs)

    async def update_data(self, data: Optional[dict] = None, **kwargs: Any) -> None:
        if data:
            kwargs.update(data)

        async with self.pool_db.acquire() as conn:
            for key, data in kwargs.items():
                await conn.execute(f"UPDATE data SET {key} = $2 WHERE id = $1;", self.key.chat_id, data)

        await self.storage.update_data(bot=self.bot, key=self.key, data=kwargs)

    async def clear(self) -> None:
        async with self.pool_db.acquire() as conn:
            await conn.execute(f"DELETE FROM data WHERE id = $1;", self.key.chat_id)

        await self.storage.set_data(bot=self.bot, key=self.key, data={})
