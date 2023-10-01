import json
from abc import ABCMeta
from dataclasses import dataclass, fields, asdict
from datetime import datetime
from types import GenericAlias

import ydb

import config


class Model:
    pool: ydb.aio.SessionPool

    class Meta(metaclass=ABCMeta):
        table_name: str
        table_schema: dict[str, str | dict]

    @classmethod
    def _get_type(cls, key: str):
        params = cls.Meta.table_schema[key]

        query_type = params['type']
        if not params.get('not_null', False):
            query_type = f"Optional<{query_type}>"

        return query_type

    @classmethod
    def _get_pks(cls):
        for key, params in cls.Meta.table_schema.items():
            if params.get('not_null', False):
                yield key

    def _denormalize(self: dataclass):
        for field in fields(self):
            value = getattr(self, field.name)

            match value:
                case str():
                    if isinstance(field.type, GenericAlias) and field.type.__origin__ in (list, dict):
                        setattr(self, field.name, json.loads(value))
                case int():
                    if field.type == datetime:
                        setattr(self, field.name, datetime.utcfromtimestamp(value))

    @classmethod
    def _normalize(cls, params: dict):
        for key, value in params.items():
            match value:
                case list() | dict():
                    params[key] = json.dumps(value)
                case datetime():
                    params[key] = int(datetime.timestamp(value))

    @classmethod
    async def _execute(cls, query: str, prepared_params: dict = None) -> ydb.convert.ResultSets:
        async with cls.pool.checkout() as session:
            if prepared_params is not None:
                query = await session.prepare(query)

            return await session.transaction(ydb.SerializableReadWrite()).execute(
                query, prepared_params, commit_tx=True
            )

    @classmethod
    async def get(cls: dataclass, **kwargs):
        return cls(**(await cls._get(**kwargs) or kwargs))

    @classmethod
    async def _get(cls, **kwargs):
        query_structures = []
        query_filters = []
        prepared_params = {}

        for key, value in kwargs.items():
            query_structures.append(f"DECLARE ${key} as {cls._get_type(key)};")
            query_filters.append(f'{key} == ${key}')
            prepared_params[f'${key}'] = value

        query_structure = '\n'.join(query_structures)
        query_filter = ' AND '.join(query_filters)

        query = (
            f"""
            PRAGMA TablePathPrefix("{config.YDB_DATABASE}");

            {query_structure}

            SELECT * FROM {cls.Meta.table_name}
            WHERE {query_filter};
            """
        )

        cls._normalize(prepared_params)
        queryset = await cls._execute(query, prepared_params)

        if queryset[0].rows:
            return queryset[0].rows[0]

    async def save(self: dataclass):
        return await self._save(**asdict(self))

    async def _save(self, **kwargs):
        query_structures = [f"{key}: {self._get_type(key)}" for key in kwargs]
        query_structure = ', '.join(query_structures)

        query = (
            f"""
            PRAGMA TablePathPrefix("{config.YDB_DATABASE}");

            DECLARE $input AS List<Struct<{query_structure}>>;

            UPSERT INTO {self.Meta.table_name} SELECT * FROM AS_TABLE($input);
            """
        )

        self._normalize(kwargs)
        return await self._execute(query, {"$input": [kwargs]})

    async def delete(self: dataclass):
        return await self._delete()

    async def _delete(self):
        query_structures = []
        query_filters = []
        prepared_params = {}

        for key in self._get_pks():
            query_structures.append(f"DECLARE ${key} as {self.Meta.table_schema[key]['type']};")
            query_filters.append(f'{key} == ${key}')
            prepared_params[f'${key}'] = getattr(self, key)

        query_structure = '\n'.join(query_structures)
        query_filter = ' AND '.join(query_filters)

        query = (
            f"""
            PRAGMA TablePathPrefix("{config.YDB_DATABASE}");

            {query_structure}

            DELETE FROM {self.Meta.table_name} 
            WHERE {query_filter};
            """
        )

        self._normalize(prepared_params)
        return await self._execute(query, prepared_params)

    @classmethod
    async def setup(cls):
        query_params = f"primary key ({', '.join(cls._get_pks())})"
        return await cls._setup(query_params)

    @classmethod
    async def _setup(cls, query_params: str):
        query_structures = [f"{key} {value['type']}" for key, value in cls.Meta.table_schema]
        query = f"create table {cls.Meta.table_name} ({', '.join(query_structures)}, {query_params});"

        async with cls.pool.checkout() as session:
            await session.execute_scheme(query)
