from typing import Any, Optional

from aiogram import Bot
from aiogram.fsm.storage.base import BaseStorage, StorageKey
from asyncpg import Pool


class DataBaseContext:
    def __init__(self, bot: Bot, key: StorageKey, storage: BaseStorage, pool_db: Pool):
        self.bot = bot
        self.key = key
        self.storage = storage

        self.pool_db = pool_db

    async def get_data(self, column: str) -> Any:
        data = (await self.storage.get_data(bot=self.bot, key=self.key)).get(column)

        if not data:
            async with self.pool_db.acquire() as conn:
                data = await conn.fetchval(f"SELECT {column} FROM data WHERE id = $1;", self.key.chat_id) or \
                       await conn.fetchval(f"SELECT {column} FROM data WHERE id = 0;")

            await self.storage.update_data(bot=self.bot, key=self.key, data={column: data or 'NULL'})

        elif data == 'NULL':
            data = None

        return data

    async def set_data(self, data: Optional[dict] = None, **kwargs: Any) -> None:
        if data:
            kwargs.update(data)

        async with self.pool_db.acquire() as conn:
            for column, data in kwargs.items():
                await conn.execute(
                    f"INSERT INTO data (id, {column}) VALUES ($1, $2) ON CONFLICT (id) DO UPDATE SET {column} = $2;",
                    self.key.chat_id, data
                )

        await self.storage.update_data(bot=self.bot, key=self.key, data=kwargs)

    async def update_data(self, data: Optional[dict] = None, **kwargs: Any) -> None:
        if data:
            kwargs.update(data)

        async with self.pool_db.acquire() as conn:
            for column, data in kwargs.items():
                await conn.execute(f"UPDATE data SET {column} = $2 WHERE id = $1;", self.key.chat_id, data)

        await self.storage.update_data(bot=self.bot, key=self.key, data=kwargs)

    async def clear(self) -> None:
        async with self.pool_db.acquire() as conn:
            await conn.execute(f"DELETE FROM data WHERE id = $1;", self.key.chat_id)

        await self.storage.set_data(bot=self.bot, key=self.key, data={})
