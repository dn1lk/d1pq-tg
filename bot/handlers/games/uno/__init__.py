import asyncio

from aiogram import Router, types
from aiogram.dispatcher.fsm.context import FSMContext
from aiogram.utils.i18n import gettext as _

from .action import UnoAction
from .data import UnoData, UnoPollKick
from .exceptions import UnoNoUsersException
from .. import close_timeout


async def uno_timeout(message: types.Message, state: FSMContext, data_uno: UnoData):
    data_uno.timer_amount -= 1

    if not data_uno.timer_amount or len(data_uno.users) == 2 and state.bot.id in data_uno.users:
        try:
            for user_id in data_uno.users:
                await data_uno.remove_user(state, user_id)
        except UnoNoUsersException:
            await data_uno.remove_user(state, tuple(data_uno.users)[0])

        await close_timeout(message, state)
    else:
        message = await message.reply(
            _("Time is over.") + " " + await data_uno.add_card(state.bot, message.chat.id, data_uno.next_user_id)
        )

        for poll_id, poll_data in data_uno.polls_kick.items():
            if data_uno.next_user_id == poll_data.user_id:
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
            user_id=data_uno.next_user_id,
            amount=0,
        )

        await asyncio.sleep(3)

        action_uno = UnoAction(message=message, state=state, data=data_uno)
        await action_uno.move()


def setup():
    router = Router(name='game:uno')

    from .. import Game

    router.message.filter(Game.uno)
    router.poll_answer.filter(Game.uno)

    from .middleware import UnoFSMContextMiddleware

    router.inline_query.outer_middleware(UnoFSMContextMiddleware())
    router.poll_answer.outer_middleware(UnoFSMContextMiddleware())

    from .user import router as user_rt
    from .core import router as core_rt

    sub_routers = (
        user_rt,
        core_rt,
    )

    for sub_router in sub_routers:
        router.include_router(sub_router)

    return router
