import asyncio
from random import choice

from aiogram import Router, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.utils.i18n import gettext as _, lazy_gettext as __

__all__ = 'Games', 'WINNER', 'timer', 'win_timeout', 'close_timeout', 'setup'


class Games(StatesGroup):
    uno = State()
    cts = State()
    rnd = State()


WINNER = (
    __("Victory for me."),
    __("I am a winner."),
    __("I am the winner in this game."),
)


def timer(state: FSMContext, coroutine, exception=None, **kwargs) -> asyncio.Task:
    async def waiter():
        raw_state = await state.get_state()

        try:
            await asyncio.sleep(60)
            if raw_state == await state.get_state():
                return await coroutine(state=state, **kwargs)
        except asyncio.CancelledError:
            if exception:
                await exception(state=state, **kwargs)

    name = f'game:{state.key.chat_id}'

    for task in asyncio.all_tasks():
        if task.get_name() == name:
            task.cancel()
            break

    return asyncio.create_task(waiter(), name=name)


async def win_timeout(message: types.Message, state: FSMContext):
    await close_timeout(message, state, answer=f'{_("Your time is up.")} {choice(WINNER)}')


async def close_timeout(message: types.Message, state: FSMContext, answer: str | None = None):
    answer = answer or choice(
        (
            _("You know I won't play with you! Maybe..."),
            _("Well don't play with me!"),
            _("I thought we were playing..."),
            _("It's too slow, I won't play with you!"),
        )
    )

    await state.clear()
    await message.reply(answer, reply_markup=types.ReplyKeyboardRemove())


def setup():
    router = Router(name='game')

    from .uno import setup as uno_rt

    from .cts import router as cts_rt
    from .rnd import router as rnd_rt
    from .rps import router as rps_rt
    from .core import router as core_rt

    sub_routers = (
        core_rt,
        uno_rt(),
        cts_rt,
        rps_rt,
        rnd_rt,
    )

    for sub_router in sub_routers:
        router.include_router(sub_router)

    return router
