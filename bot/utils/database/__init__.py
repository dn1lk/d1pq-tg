from json import dumps, loads

from asyncpg import Pool, Connection, create_pool

from bot import config


async def init_connection(conn: Connection):
    await conn.set_type_codec(
        typename='json',
        encoder=dumps,
        decoder=loads,
        schema='pg_catalog'
    )


async def setup() -> Pool:
    pool: Pool = await create_pool(config.heroku.database_url, max_size=20, init=init_connection)

    async with pool.acquire() as conn:
        await conn.execute(
            """CREATE TABLE IF NOT EXISTS data (
                ids             BIGINT              PRIMARY KEY NOT NULL,
                locales         TEXT,                
                messages        TEXT ARRAY,
                stickers        TEXT ARRAY          DEFAULT '{TextAnimated}',
                members         BIGINT ARRAY,
                commands        JSON,
                chance          FLOAT               DEFAULT 2,
                accuracy        SMALLINT            DEFAULT 3
            );"""
        )

        await conn.execute(
            f"INSERT INTO data (ids) VALUES (0) ON CONFLICT (ids) DO NOTHING;"
        )

    return pool
