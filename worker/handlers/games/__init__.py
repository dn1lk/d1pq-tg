from asyncio import sleep

from aiogram import Router, types
from aiogram.dispatcher.fsm.context import FSMContext
from aiogram.dispatcher.fsm.state import StatesGroup, State
from aiogram.utils.i18n import gettext as _

from worker import config


class GameState(StatesGroup):
    UNO = State('uno')
    CTS = State('cts')
    RND = State('rnd')
    RPS = State('rps')


async def game_timer(message: types.Message, state: FSMContext) -> None:
    await sleep(60 * 60)

    if await state.get_state() in GameState.__states__:
        await message.reply(_("You know I won't play with you! Maybe..."))
        await state.clear()


def get_game_cts(locale: str) -> list:
    with open(config.BASE_DIR / 'locales' / locale / 'cities.txt', 'r', encoding='utf8') as f:
        return f.read().splitlines()


def setup():
    router = Router(name='game')

    from .uno import setup as uno_rt
    from .cts import router as cts_rt
    from .rnd import router as rnd_rt
    from .rps import router as rps_rt
    from .start import router as start_rt

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
