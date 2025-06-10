import json
from typing import Annotated, ClassVar

import ydb

import misc
from utils.database import types
from utils.database.base import Column

from .base import WithDates, WithToken


class MainSettings(WithDates, WithToken):
    __tablename__: ClassVar[str] = "main_settings"

    __slots__ = (
        "chat_id",
        "created_at",
        "locale",
        "token",
        "updated_at",
        "with_commands",
        "with_members",
    )

    chat_id: Annotated[int, Column(types.Int64, is_primary_key=True)]
    locale: Annotated[str | None, Column(types.Utf8, is_null=True)]
    with_members: Annotated[bool, Column(types.Bool, default=True)]
    with_commands: Annotated[bool, Column(types.Bool, default=True)]

    @property
    def members(self) -> list[int]:
        assert self.with_members is True, "members disabled"

        filename = self._get_filename(f"{self.chat_id}:members")
        encryptor = self._encryptor

        members = self._read_file(misc.MNT_PATH / "members" / filename, encryptor)
        members = json.loads(members) if members else []

        return members

    @members.setter
    def members(self, members: list[int]) -> None:
        assert self.with_members is True, "members disabled"

        filename = self._get_filename(f"{self.chat_id}:members")
        encryptor = self._encryptor

        self._write_file(misc.MNT_PATH / "members" / filename, encryptor, json.dumps(members))

    @members.deleter
    def members(self) -> None:
        assert self.with_members is False, "members enabled"

        filename = self._get_filename(f"{self.chat_id}:members")
        self._remove_file(misc.MNT_PATH / "members" / filename)

    @property
    def commands(self) -> dict[str, str]:
        assert self.with_commands is True, "commands disabled"

        filename = self._get_filename(f"{self.chat_id}:commands")
        encryptor = self._encryptor

        commands = self._read_file(misc.MNT_PATH / "commands" / filename, encryptor)
        commands = json.loads(commands) if commands else {}

        return commands

    @commands.setter
    def commands(self, commands: dict[str, str]) -> None:
        assert self.with_commands is True, "commands disabled"

        filename = self._get_filename(f"{self.chat_id}:commands")
        encryptor = self._encryptor

        self._write_file(misc.MNT_PATH / "commands" / filename, encryptor, json.dumps(commands))

    @commands.deleter
    def commands(self) -> None:
        assert self.with_commands is False, "commands enabled"

        filename = self._get_filename(f"{self.chat_id}:commands")
        self._remove_file(misc.MNT_PATH / "commands" / filename)

    @classmethod
    async def setup(cls) -> None:
        (misc.MNT_PATH / "members").mkdir(parents=True, exist_ok=True)
        (misc.MNT_PATH / "commands").mkdir(parents=True, exist_ok=True)

        return await super().setup()

    async def delete(self) -> ydb.convert.ResultSets | None:
        self.with_members = False
        del self.members

        self.with_commands = False
        del self.commands

        return await super().delete()
