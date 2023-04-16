from aiogram.fsm.context import FSMContext
from pydantic import BaseModel


class PlayData(BaseModel):
    async def set_data(self, state: FSMContext):
        await state.set_data(self.dict())

    @classmethod
    async def get_data(cls, state: FSMContext) -> "PlayData":
        data = await state.get_data()
        if data:
            return cls(**data)
