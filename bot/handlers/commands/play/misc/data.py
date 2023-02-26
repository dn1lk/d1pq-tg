from dataclasses import dataclass, asdict

from aiogram.fsm.context import FSMContext


@dataclass
class PlayData:
    async def set_data(self, state: FSMContext):
        await state.set_data(asdict(self))

    @classmethod
    async def get_data(cls, state: FSMContext) -> "PlayData":
        data = await state.get_data()
        return cls(**data)
