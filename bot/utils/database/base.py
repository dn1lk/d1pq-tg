import inspect
from collections.abc import Callable
from dataclasses import dataclass, field
from functools import lru_cache
from typing import Any, ClassVar, Self

import ydb

import config

from .types.base import BaseType

type CT = Any


@dataclass(slots=True, frozen=True)
class Column[T: BaseType[CT]]:
    type: type[T]
    is_primary_key: bool = False
    is_null: bool = False
    default: T | Callable[..., T] | None = None
    on_update: T | Callable[..., T] | None = None

    @property
    def query_type(self) -> str:
        _type = self.type.__queryname__()

        if self.is_null:
            return f"Optional<{_type}>"
        return _type

    def __call__(self, value: T | Callable[..., T] | None) -> T | None:
        assert issubclass(self.type, BaseType), f"incorrect column type: {self.type}"
        return value if value is None else self.type.deserialize(value)


@dataclass(slots=True, frozen=True)
class Index:
    name: str
    keys: list
    covers: list = field(default_factory=list)


class Model:
    __pool__: ClassVar[ydb.aio.SessionPool]

    __tablename__: ClassVar[str] = ""
    __indices__: ClassVar[list[Index]] = []

    def __init__(self, **kwargs: CT) -> None:
        self.columns_changed: set[str] = set()
        for name, column in self._get_columns().items():
            value = kwargs.get(name)
            super().__setattr__(name, column(value))

    def __setattr__(self, name: str, value: BaseType[CT] | None) -> None:
        if name in self._get_columns():
            self.columns_changed.add(name)

        return super().__setattr__(name, value)

    @classmethod
    @lru_cache
    def _get_columns(cls) -> dict[str, Column[BaseType[CT]]]:
        columns: dict[str, Column[BaseType[CT]]] = {}
        for obj in cls.__mro__:
            for name, _field in inspect.get_annotations(obj).items():
                for column in getattr(_field, "__metadata__", ()):
                    if isinstance(column, Column):
                        columns[name] = column
                        break

        return columns

    @classmethod
    @lru_cache
    def _get_pks(cls) -> dict[str, Column[BaseType[CT]]]:
        pks = {name: column for name, column in cls._get_columns().items() if column.is_primary_key}
        return pks

    @classmethod
    def _serialize(cls, params: dict[str, BaseType[CT] | None]) -> None:
        for param, value in params.items():
            params[param] = None if value is None else value.serialize()

    @classmethod
    async def _execute(
        cls,
        query: str,
        prepared_params: list[dict[str, Any]] | dict[str, Any] | None = None,
    ) -> ydb.convert.ResultSets:
        async with cls.__pool__.checkout() as session:
            if prepared_params is not None:
                query = await session.prepare(query)

            transaction = session.transaction(ydb.SerializableReadWrite())
            return await transaction.execute(query, prepared_params, commit_tx=True)

    @classmethod
    async def _filter(cls, **kwargs: CT) -> list:
        query_structures = []
        query_filters = []
        prepared_params: dict[str, BaseType[CT] | None] = {}

        for name, column in cls._get_columns().items():
            if name in kwargs:
                query_structures.append(f"declare ${name} as {column.query_type};")
                query_filters.append(f"{name} == ${name}")
                prepared_params[f"${name}"] = column(kwargs[name])

        query_structure = "\n".join(query_structures)
        query_filter = " and ".join(query_filters)

        query = (
            f"pragma TablePathPrefix('{config.YDB_DATABASE}');"
            f" {query_structure}"
            f" select * from {cls.__tablename__}"
            f" where {query_filter};"
        )

        cls._serialize(prepared_params)
        queryset = await cls._execute(query, prepared_params)

        return queryset[0].rows

    @classmethod
    async def filter(cls, **kwargs: CT) -> list[Self]:
        datas = await cls._filter(**kwargs)
        return [cls(**data) for data in datas]

    @classmethod
    async def _get(cls, **kwargs: CT) -> dict[str, CT] | None:
        datas = await cls._filter(**kwargs)
        if datas:
            return datas[0]
        return None

    @classmethod
    async def get(cls, **kwargs: CT) -> Self:
        data = await cls._get(**kwargs)
        if data is None:
            self = cls(**kwargs)
            for name, column in cls._get_columns().items():
                if column.default is not None:
                    setattr(self, name, column.default() if callable(column.default) else column.default)

            return self
        return cls(**data)

    async def _save(self, **kwargs: BaseType[CT] | None) -> ydb.convert.ResultSets:
        query_structures = []
        for name, column in self._get_columns().items():
            if name in kwargs:
                query_structures.append(f"{name}: {column.query_type}")

        query_structure = ", ".join(query_structures)

        query = (
            f"pragma TablePathPrefix('{config.YDB_DATABASE}');"
            f" declare $input as List<Struct<{query_structure}>>;"
            f" upsert into {self.__class__.__tablename__} select * from AS_TABLE($input);"
        )

        self._serialize(kwargs)
        rows = await self._execute(query, {"$input": [kwargs]})

        self.columns_changed.clear()
        return rows

    async def save(self, *columns_changed: str) -> ydb.convert.ResultSets:
        for name, column in self._get_columns().items():
            if column.on_update is not None:
                setattr(self, name, column.on_update() if callable(column.on_update) else column.on_update)
            elif column.is_null is False:
                self.columns_changed.add(name)

        if columns_changed:
            self.columns_changed = self.columns_changed.union(columns_changed)

        kwargs = {name: getattr(self, name) for name in self.columns_changed.union(self._get_pks())}
        return await self._save(**kwargs)

    async def _delete(self) -> ydb.convert.ResultSets:
        query_structures = []
        query_filters = []
        prepared_params = {}

        for name, column in self._get_pks().items():
            query_structures.append(f"declare ${name} as {column.query_type};")
            query_filters.append(f"{name} == ${name}")
            prepared_params[f"${name}"] = getattr(self, name)

        query_structure = "\n".join(query_structures)
        query_filter = " and ".join(query_filters)

        query = (
            f"pragma TablePathPrefix('{config.YDB_DATABASE}');"
            f" {query_structure}"
            f" delete from {self.__class__.__tablename__}"
            f" where {query_filter};"
        )

        self._serialize(prepared_params)
        rows = await self._execute(query, prepared_params)

        self.columns_changed.clear()
        return rows

    async def delete(self) -> ydb.convert.ResultSets:
        return await self._delete()

    @classmethod
    async def _setup(cls, query_params: str) -> None:
        query_structure = []
        for name, column in cls._get_columns().items():
            query_column = f"{name} {column.type.__queryname__()}"
            query_column += " null" if column.is_null else " not null"
            if not (column.default is None or callable(column.default)):
                query_column += f' default {column.type.__queryname__()}("{column.default.serialize()}")'

            query_structure.append(query_column)

        query_structure = ", ".join(query_structure)
        query_structure += ","

        if cls.__indices__:
            query_indices = []
            for index in cls.__indices__:
                query_index_fields = ", ".join(index.keys)
                query_index = f"index {index.name} global on ({query_index_fields})"

                if index.covers:
                    query_index_covers = ", ".join(index.covers)
                    query_index += f" cover {query_index_covers}"

                query_indices.append(query_index)

            query_indices = ", ".join(query_indices)
            query_indices += ","
        else:
            query_indices = ""

        query = f"create table {cls.__tablename__} ({query_structure} {query_indices} {query_params});"
        async with cls.__pool__.checkout() as session:
            await session.execute_scheme(query)

    @classmethod
    async def setup(cls) -> None:
        primary_keys = ", ".join(name for name in cls._get_pks())

        query_params = f"primary key ({primary_keys})"
        return await cls._setup(query_params)
