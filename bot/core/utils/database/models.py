import json
from dataclasses import dataclass, field
from datetime import datetime

from .base import Model

__all__ = (
    "Model",
    "MainSettings",
    "GenSettings",
    "DEFAULT_STICKER_SET",
)


DEFAULT_STICKER_SET = "TextAnimated"


@dataclass(slots=True, kw_only=True)
class WithDates(Model):
    updated: datetime = field(default_factory=datetime.utcnow)
    created: datetime = field(default_factory=datetime.utcnow)

    def __post_init__(self):
        if isinstance(self.updated, int):
            self.updated = datetime.fromtimestamp(self.updated)
        if isinstance(self.created, int):
            self.created = datetime.fromtimestamp(self.created)

    async def save(self):
        self.updated = datetime.utcnow()
        return await Model.save(self)


@dataclass(slots=True)
class MainSettings(WithDates):
    chat_id: int
    locale: str = None
    members: list[int] = field(default_factory=list)
    commands: dict[str, str] = field(default_factory=dict)

    class Meta:
        table_name = 'main_settings'
        table_schema = {
            'chat_id': {'type': 'Int64', 'not_null': True},
            'locale': {'type': 'Utf8'},
            'members': {'type': 'Json'},
            'commands': {'type': 'Json'},
            'updated': {'type': 'Datetime'},
            'created': {'type': 'Datetime'},
        }

    def __post_init__(self):
        WithDates.__post_init__(self)

        if isinstance(self.members, str):
            self.members = json.loads(self.members)
        if isinstance(self.commands, str):
            self.commands = json.loads(self.commands)


@dataclass(slots=True)
class GenSettings(WithDates):
    chat_id: int
    chance: float = 0.1
    accuracy: int = 2
    messages: list[str] = f'["{DEFAULT_STICKER_SET}"]'
    stickers: list[str] = field(default_factory=list)

    class Meta:
        table_name = 'gen_settings'
        table_schema = {
            'chat_id': {'type': 'Int64', 'not_null': True},
            'chance': {'type': 'Float'},
            'accuracy': {'type': 'Uint8'},
            'messages': {'type': 'Json'},
            'stickers': {'type': 'Json'},
            'updated': {'type': 'Datetime'},
            'created': {'type': 'Datetime'},
        }

    def __post_init__(self):
        WithDates.__post_init__(self)

        if isinstance(self.messages, str):
            self.messages = json.loads(self.messages)
        if isinstance(self.stickers, str):
            self.stickers = json.loads(self.stickers)
