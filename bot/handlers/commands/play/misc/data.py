from dataclasses import dataclass, asdict, is_dataclass, fields
from types import GenericAlias

from aiogram.fsm.context import FSMContext


def asdataclass(obj, data):
    if not is_dataclass(obj):
        return data
    if not data:
        return data

    values = {}
    for f in fields(obj):
        if isinstance(f.type, GenericAlias) and f.type.__origin__ == list:
            values[f.name] = [asdataclass(f.type.__args__[0], d2) for d2 in data[f.name]]
        else:
            values[f.name] = asdataclass(f.type, data[f.name])
    return obj(**values)


@dataclass
class PlayData:
    async def set_data(self, state: FSMContext):
        await state.set_data(asdict(self))

    @classmethod
    async def get_data(cls, state: FSMContext) -> "PlayData":
        return asdataclass(cls, await state.get_data())
