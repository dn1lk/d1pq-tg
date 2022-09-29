import asyncio
from random import choice

from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from aiogram.utils.i18n import gettext as _, lazy_gettext as __

from .cards import UnoColors
from .data import UnoData, UnoPollKick
from .exceptions import UnoNoUsersException
from .process import post
from .. import close_timeout


UNO = __("UNO!")
DRAW_CARD = __("Take a card.")


async def uno_timeout(message: types.Message, state: FSMContext):
    data_uno: UnoData = UnoData(**(await state.get_data())['uno'])
    data_uno.timer_amount -= 1

    if not data_uno.timer_amount or len(data_uno.users) == 2 and state.bot.id in data_uno.users:
        try:
            for user_id in tuple(data_uno.users):
                await data_uno.remove_user(state, user_id)
        except UnoNoUsersException:
            await data_uno.remove_user(state, tuple(data_uno.users)[0])

        await close_timeout(message, state)
    else:
        answer = _("Time is over.") + " " + await data_uno.add_card(state.bot, message.entities[0].user)

        if data_uno.current_card.color is UnoColors.black:
            color = choice(UnoColors.get_names(exclude={UnoColors.black.name}))
            await message.answer(_("Current color: {color}").format(color=color))

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
            user_id=data_uno.current_user_id,
            amount=0,
        )

        await asyncio.sleep(3)
        await post(message, data_uno, state, answer)


def setup():
    router = Router(name='game:uno')

    from .. import Game, keyboards as k

    router.message.filter(Game.uno)
    router.poll_answer.filter(Game.uno)
    router.callback_query.filter(k.Games.filter(F.game == 'uno'))

    from .middleware import UnoFSMContextMiddleware

    router.inline_query.outer_middleware(UnoFSMContextMiddleware())
    router.poll_answer.outer_middleware(UnoFSMContextMiddleware())

    from .action import router as action_rt
    from .user import router as user_rt
    from .core import router as core_rt
    from .inline import router as inline_rt
    from .poll import router as poll_rt

    sub_routers = (
        action_rt,
        user_rt,
        core_rt,
        inline_rt,
        poll_rt,
    )

    for sub_router in sub_routers:
        router.include_router(sub_router)

    return router
