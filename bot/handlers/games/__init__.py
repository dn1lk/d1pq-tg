from asyncio import create_task
from random import choice

from aiogram import Router, types
from aiogram.dispatcher.fsm.context import FSMContext
from aiogram.dispatcher.fsm.state import StatesGroup, State
from aiogram.utils.i18n import gettext as _, lazy_gettext as __

from bot import config


class Game(StatesGroup):
    uno = State()
    cts = State()
    rnd = State()
    rps = State()


CTS_WIN = (
    __("Victory for me."),
    __("I am a winner."),
    __("I am the winner in this game."),
)


def get_cts(locale: str) -> list:
    with open(config.BASE_DIR / 'locales' / locale / 'cities.txt', 'r', encoding='utf8') as f:
        return f.read().splitlines()


def timer(message: types.Message, state: FSMContext, coroutine):
    async def waiter():
        current_state = (await state.get_state()).lower().split(':', maxsplit=1)

        if await state.timer(timeout=60, **{current_state[0]: current_state[1]}):
            if current_state[1] == await state.get_state() and current_state[1] != 'uno':
                await state.set_state()
                await coroutine(message)

            return True

    return create_task(waiter())


async def cts_timeout(message: types.Message):
    await message.reply(
        text=_("Your time is up. ") + str(choice(CTS_WIN)),
    )


async def rps_timeout(message):
    await message.reply(
        choice(
            (
                _("You know I won't play with you! Maybe..."),
                _("Well don't play with me!"),
                _("I thought we were playing..."),
                _("It's too slow, I won't play with you!"),
            )
        ),
        reply_markup=types.ReplyKeyboardRemove(),
    )


def setup():
    router = Router(name='game')

    from .uno import setup as uno_rt
    from .cts import router as cts_rt
    from .rnd import router as rnd_rt
    from .rps import router as rps_rt
    from .core import router as start_rt

    sub_routers = (
        uno_rt(),
        cts_rt,
        rnd_rt,
        rps_rt,
        start_rt,
    )

    for sub_router in sub_routers:
        router.include_router(sub_router)

    return router
