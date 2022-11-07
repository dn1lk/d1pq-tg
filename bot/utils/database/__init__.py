from asyncpg import Pool, Connection, create_pool


async def init_connection(conn: Connection):
    from json import dumps, loads
    await conn.set_type_codec(
        typename='json',
        encoder=dumps,
        decoder=loads,
        schema='pg_catalog'
    )


async def setup() -> Pool:
    from bot import config
    pool: Pool = await create_pool(config.heroku.database_url, max_size=20, init=init_connection)

    async with pool.acquire() as conn:
        await conn.execute(
            """CREATE TABLE IF NOT EXISTS record (
                id              BIGINT              PRIMARY KEY NOT NULL,
                locale          TEXT,                
                messages        TEXT ARRAY,
                stickers        TEXT ARRAY          DEFAULT '{TextAnimated}',
                members         BIGINT ARRAY,
                commands        JSON,
                chance          FLOAT               DEFAULT 2,
                accuracy        SMALLINT            DEFAULT 3
            );"""
        )

        await conn.execute(f"INSERT INTO record (id) VALUES (0) ON CONFLICT (id) DO NOTHING;")

    return pool
