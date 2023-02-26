class PlayData(BaseModel):
    games = {}

    @staticmethod
    async def get_key(state: FSMContext):
        return f'{state.key.chat_id}:{await state.get_state()}'

    @classmethod
    async def get_data(cls, state: FSMContext) -> "GamesData":
        data = cls.games.get(await cls.get_key(state)) or await state.get_data()

        if data:
            return cls(**data)

    async def set_data(self, state: FSMContext):
        await state.set_data(self.dict())
