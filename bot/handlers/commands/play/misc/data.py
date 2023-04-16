from dataclasses import asdict, is_dataclass

from aiogram.fsm.context import FSMContext
from pydantic import BaseModel


class PlayData(BaseModel):
    async def set_data(self, state: FSMContext):
        data = {key: asdict(value) if is_dataclass(value) else value for key, value in self}
        await state.set_data(data)

    @classmethod
    async def get_data(cls, state: FSMContext) -> "PlayData":
        data = await state.get_data()

        if data:
            return cls(**await state.get_data())
