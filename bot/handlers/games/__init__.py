from enum import Enum
from random import choice

from aiogram import Router, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.utils.i18n import gettext as _, lazy_gettext as __
from pydantic import BaseModel


class Games(Enum):
    CTS = 'cts', 'грд'
    RND = 'rnd', 'рнд'
    RPS = 'rps', 'кнб'
    UNO = 'uno', 'уно'


class GamesStates(StatesGroup):
    CTS = State()
    RND = State()
    UNO = State()


class GamesData(BaseModel):
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


WINNER = (
    __("Victory for me."),
    __("I am a winner."),
    __("I am the winner in this game."),
)

CLOSE = (
    __("You know I won't play with you! Maybe..."),
    __("Well don't play with me!"),
    __("I thought we were playing..."),
    __("It's too slow, I won't play with you!"),
)


async def win_timeout(message: types.Message, state: FSMContext):
    await close_timeout(message, state, answer=f'{_("Your time is up.")} {choice(WINNER)}')


async def close_timeout(message: types.Message, state: FSMContext, answer: str | None = None):
    answer = answer or choice(CLOSE).value

    await state.clear()
    await message.reply(answer, reply_markup=types.ReplyKeyboardRemove())


def setup(router: Router):
    from .cts import setup as cts_setup
    from .rnd import setup as rnd_setup
    from .rps import setup as rps_setup
    from .uno import setup as uno_setup

    uno_setup(router)
    rps_setup(router)
    rnd_setup(router)
    cts_setup(router)
