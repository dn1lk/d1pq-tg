from typing import Any, Optional

import asyncpg
from aiogram.dispatcher.fsm.context import FSMContext

from worker import config


class SQL:
    def __init__(self, pool: asyncpg.pool):
        self.pool: asyncpg.Pool = pool

    async def get_data(self, chat_id: int, key: str, state: Optional[FSMContext] = None) -> Any:
        result = None

        if state:
            result = (await state.get_data()).get(key)

        if not result:
            async with self.pool.acquire() as conn:
                result = await conn.fetchval(f"""SELECT {key} FROM data WHERE ids = $1;""", chat_id) or \
                         await conn.fetchval(f"""SELECT {key} FROM data WHERE ids = 0;""")

                if state:
                    await state.update_data({key: result or 'NULL'})

        if result == 'NULL':
            result = None

        return result

    async def set_data(self, chat_id: int, key: str, values, state: Optional[FSMContext] = None) -> None:
        async with self.pool.acquire() as conn:
            await conn.execute(
                f"INSERT INTO data (ids, {key}) VALUES ($1, $2) ON CONFLICT (ids) DO UPDATE SET {key} = $2;",
                chat_id, values
            )

            if state:
                await state.update_data({key: values})

    async def update_data(self, chat_id: int, key: str, values, state: Optional[FSMContext] = None) -> None:
        async with self.pool.acquire() as conn:
            await conn.execute(f"UPDATE data SET {key} = $2 WHERE ids = $1;", chat_id, values)

            if state:
                await state.update_data({key: values})

    async def del_data(self, chat_id: int, state: Optional[FSMContext] = None) -> None:
        async with self.pool.acquire() as conn:
            await conn.execute(f"DELETE FROM data WHERE ids = $1;", chat_id)

            if state:
                await state.clear()


async def setup():
    pool = await asyncpg.create_pool(config.heroku.database_url, max_size=20)

    await pool.execute(
        """CREATE TABLE IF NOT EXISTS data (
            ids             NUMERIC             PRIMARY KEY NOT NULL,
            members         JSON,
            locales         TEXT,
            commands        JSON,
            messages        TEXT ARRAY,
            stickers        TEXT                DEFAULT 'TextAnimated',
            chance          NUMERIC             DEFAULT 2,
            accuracy        INT                 DEFAULT 3
        );"""
    )
    await pool.execute(
        f"INSERT INTO data (ids) VALUES (0) ON CONFLICT (ids) DO NOTHING;"
    )

    return SQL(pool)
