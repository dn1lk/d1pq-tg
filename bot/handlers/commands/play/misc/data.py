from typing import Self

from aiogram.fsm.context import FSMContext
from pydantic import BaseModel


class PlayData(BaseModel):
    async def set_data(self, state: FSMContext) -> None:
        await state.set_data(self.model_dump())

    @classmethod
    async def get_data(cls, state: FSMContext) -> Self | None:
        data = await state.get_data()
        if data:
            return cls(**data)
        return None
