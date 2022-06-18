import asyncio
from random import choice

from aiogram import Router, types
from aiogram.dispatcher.fsm.context import FSMContext
from aiogram.dispatcher.fsm.state import StatesGroup, State
from aiogram.utils.i18n import gettext as _, lazy_gettext as __

from bot import config
from .uno.action import UnoAction
from .uno.data import UnoData, UnoPollKick
from .uno.exceptions import UnoNoUsersException


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
        raw_state = await state.get_state()

        if await state.timer(timeout=60, game=str(raw_state).lower().split(':', maxsplit=1)[-1]):
            if raw_state == await state.get_state():
                return await coroutine(state=state, **kwargs)

    return asyncio.create_task(waiter(), name=f'game:{state.key.chat_id}:waiter')


async def win_timeout(message: types.Message, state: FSMContext):
    await close_timeout(message, state, answer=_("Your time is up. ") + str(choice(WINNER)))


async def close_timeout(message: types.Message, state: FSMContext, answer: str | None = None):
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


async def uno_timeout(message: types.Message, state: FSMContext, data_uno: UnoData):
    data_uno.timer_amount -= 1

    if not data_uno.timer_amount or len(data_uno.users) == 2 and state.bot.id in data_uno.users:
        try:
            for user_id in data_uno.users:
                await data_uno.user_remove(state, user_id)
        except UnoNoUsersException:
            await data_uno.user_remove(state, tuple(data_uno.users)[0])

        await close_timeout(message, state)

    else:
        message = await message.reply(_("Time is over.") + " " + await data_uno.user_card_add(state.bot))

        for poll_id, poll_data in data_uno.polls_kick.items():
            if data_uno.next_user.id == poll_data.user_id:
                await state.bot.delete_message(message.chat.id, poll_data.message_id)
                del data_uno.polls_kick[poll_id]
                break

        poll = await message.answer_poll(
            _("Kick a player from the game?"),
            options=[_("Yes"), _("No, keep playing")],
            is_anonymous=False,
        )

        data_uno.polls_kick[poll.poll.id] = UnoPollKick(
            message_id=poll.message_id,
            user_id=data_uno.next_user.id,
            amount=0,
        )

        await asyncio.sleep(3)

        action = UnoAction(message=message, state=state, data=data_uno)

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
