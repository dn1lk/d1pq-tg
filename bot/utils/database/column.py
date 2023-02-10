from asyncpg import Pool, Record


class Column:
    def __init__(self, pool: Pool, defaults: Record, name: str):
        self.__pool = pool
        self.__default = defaults[name]

        self.__name = name

    def __str__(self) -> str:
        return self.__name

    async def get(self, chat_id: int):
        async with self.__pool.acquire() as connection:
            return await connection.fetchval(f"select {self} from data where id = $1;", chat_id) or self.__default

    async def set(self, chat_id: int, data):
        async with self.__pool.acquire() as connection:
            await connection.execute(
                f"""
                insert into data(id, {self})
                    values ($1, $2)
                    on conflict (id)
                        do update set {self} = $2;
                """,
                chat_id, data
            )

    async def update(self, chat_id: int, data):
        async with self.__pool.acquire() as connection:
            await connection.execute(f"update data set {self} = $2 where id = $1", chat_id, data)


class ArrayColumn(Column):
    async def cat(self, chat_id: int, data: list):
        async with self.__pool.acquire() as connection:
            return await connection.execute(
                f"""
                insert into data(id, {self})
                    values ($1, $2)
                    on conflict (id)
                        do update set {self} = array_cat({self}, $2)
                    returning {self};
                """,
                chat_id, data
            )

    async def remove(self, chat_id: int, data):
        async with self.__pool.acquire() as connection:
            return await connection.execute(
                f"""
                update data
                    set {self} = array_remove({self}, $2)
                    where id = $1
                    returning {self};
                """,
                chat_id, data
            )
