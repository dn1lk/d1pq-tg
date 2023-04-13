from dataclasses import dataclass

from asyncpg import Pool, Record, Connection, create_pool

from .column import Column, ArrayColumn


@dataclass
class SQLContext:
    _pool: Pool
    _defaults: Record

    def __post_init__(self):
        for column in ('id', 'locale', 'commands', 'chance', 'accuracy'):
            setattr(self, column, Column(self._pool, self._defaults[column], column))

        for column_array in ('messages', 'stickers', 'members'):
            setattr(self, column_array, ArrayColumn(self._pool, self._defaults[column], column_array))

    def __getitem__(self, item: str) -> Column:
        column = self.__getattribute__(item)

        if isinstance(column, Column):
            return column

        raise TypeError(f'SQLContext: unexpected column: {item}')

    async def clear(self, chat_id: int):
        async with self._pool.acquire() as connection:
            await connection.execute("delete from data where id = $1;", chat_id)

    @classmethod
    async def setup(cls, database_url: str) -> "SQLContext":
        async def init_connection(conn: Connection):
            from json import dumps, loads
            await conn.set_type_codec(
                typename='json',
                encoder=dumps,
                decoder=loads,
                schema='pg_catalog'
            )

        pool = await create_pool(database_url, max_size=20, init=init_connection)

        async with pool.acquire() as connection:
            await connection.execute(
                """
                create table if not exists data(
                    id          bigint      primary key not null,
                    locale      name,
                    messages    text[],
                    stickers    name[]      default '{TextAnimated}',
                    members     bigint[],
                    commands    json,
                    chance      smallint    default 10,
                    accuracy    smallint    default 2
                );
                """,
            )

            await connection.execute("insert into data (id) values (0) on conflict (id) do nothing;")
            defaults = await connection.fetchrow(f"select * from data where id = 0;")

        return SQLContext(_pool=pool, _defaults=defaults)

    async def close(self):
        await self._pool.close()
