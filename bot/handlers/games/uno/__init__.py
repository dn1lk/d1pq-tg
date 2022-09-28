import asyncio
from random import choice

from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from aiogram.utils.i18n import gettext as _, lazy_gettext as __

from .action import UnoAction
from .cards import UnoColors
from .data import UnoData, UnoPollKick
from .exceptions import UnoNoUsersException
from .. import close_timeout


UNO = __("UNO!")
DRAW_CARD = __("Take a card.")


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

        if data_uno.current_card.special.color:
            color = choice(UnoColors.names(exclude={UnoColors.black.name}))
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
            user_id=data_uno.next_user_id,
            amount=0,
        )

        await asyncio.sleep(3)

        action_uno = UnoAction(message=message, state=state, data=data_uno)
        await action_uno.move()


def setup():
    router = Router(name='game:uno')

    from .. import Game, keyboards as k

    router.message.filter(Game.uno)
    router.poll_answer.filter(Game.uno)
    router.callback_query.filter(k.Games.filter(F.game == 'uno'))

    from .middleware import UnoFSMContextMiddleware

    router.inline_query.outer_middleware(UnoFSMContextMiddleware())
    router.poll_answer.outer_middleware(UnoFSMContextMiddleware())

    from .user import router as user_rt
    from .core import router as core_rt
    from .inline import router as inline_rt
    from .poll import router as poll_rt

    sub_routers = (
        user_rt,
        core_rt,
        inline_rt,
        poll_rt,
    )

    for sub_router in sub_routers:
        router.include_router(sub_router)

    return router
