import asyncio
from random import choice
from typing import Optional

from aiogram import Router, types
from aiogram.dispatcher.fsm.context import FSMContext
from aiogram.dispatcher.fsm.state import StatesGroup, State
from aiogram.utils.i18n import gettext as _, lazy_gettext as __

from bot import config
from .uno.action import UnoAction
from .uno.manager import UnoManager, UnoKickPoll


class Game(StatesGroup):
    uno = State()
    cts = State()
    rnd = State()
    rps = State()


WINNER = (
    __("Victory for me."),
    __("I am a winner."),
    __("I am the winner in this game."),
)


def get_cts(locale: str) -> list:
    with open(config.BASE_DIR / 'locales' / locale / 'cities.txt', 'r', encoding='utf8') as f:
        return f.read().splitlines()


def timer(state: FSMContext, coroutine, **kwargs) -> asyncio.Task:
    async def waiter():
        state_raw = await state.get_state()

        if await state.timer(timeout=60, game=(state_raw or 'game:none').lower().split(':', maxsplit=1)[1]):
            if state_raw == await state.get_state():
                return await coroutine(state=state, **kwargs)

    return asyncio.create_task(waiter())


async def win_timeout(message: types.Message, state: FSMContext):
    await close_timeout(message, state, answer=_("Your time is up. ") + str(choice(WINNER)))


async def close_timeout(message: types.Message, state: FSMContext, answer: Optional[str] = None):
    answer = answer or choice(
            (
                _("You know I won't play with you! Maybe..."),
                _("Well don't play with me!"),
                _("I thought we were playing..."),
                _("It's too slow, I won't play with you!"),
            )
    )

    await message.reply(answer, reply_markup=types.ReplyKeyboardRemove())
    await state.set_state()


async def uno_timeout(message: types.Message, state: FSMContext, data_uno: UnoManager):
    if len(data_uno.users) != 2 and state.bot.id in data_uno.users.keys():
        await close_timeout(message, state)
        await data_uno.user_remove(state)
    else:
        message = await message.reply(_("Время вышло.") + " " + await data_uno.user_card_add(state.bot))
        for poll_id, poll_data in data_uno.kick_polls.items():
            if data_uno.current_user.id == poll_data.user_id:
                await state.bot.delete_message(state.key.chat_id, poll_data.message_id)
                del data_uno.kick_polls[poll_id]
                break

        poll = await message.answer_poll(
            _("Исключить игрока из игры?"),
            options=[_("Yes"), _("No, keep playing")],
            is_anonymous=False,
        )

        data_uno.kick_polls[poll.poll.id] = UnoKickPoll(
            message_id=poll.message_id,
            user_id=data_uno.current_user.id,
            amount=0,
        )

        await state.update_data(uno=data_uno)

        action = UnoAction(message, state, data_uno)

        await asyncio.sleep(3)

        await action.move()
        await state.update_data(uno=action.data)


def setup():
    router = Router(name='game')

    from .uno import setup as uno_rt
    from .cts import router as cts_rt
    from .rnd import router as rnd_rt
    from .rps import router as rps_rt
    from .core import router as core_rt

    sub_routers = (
        uno_rt(),
        cts_rt,
        rnd_rt,
        rps_rt,
        core_rt,
    )

    for sub_router in sub_routers:
        router.include_router(sub_router)

    return router
