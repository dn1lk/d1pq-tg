import asyncio
from random import choice

from aiogram import types
from aiogram.fsm.context import FSMContext
from aiogram.utils.i18n import gettext as _

from .cards import UnoCard, UnoEmoji, UnoColors, get_cards
from .data import UnoData, UnoUser
from .bot import UnoBot
from .exceptions import UnoNoUsersException


async def uno_timeout(message: types.Message, state: FSMContext):
    data_uno: UnoData = UnoData(**(await state.get_data())['uno'])
    data_uno.timer_amount -= 1

    if data_uno.current_card and data_uno.current_card.color is UnoColors.black:
        data_uno.current_card.color = choice(tuple(UnoColors)[:-1])
        await message.edit_text(_("Current color: {color}").format(color=data_uno.current_card.color.word))

    if not data_uno.timer_amount or len(data_uno.users) == 2 and state.bot.id in data_uno.users:
        await data_uno.finish(state)

        from ... import close_timeout

        await close_timeout(message, state)
    else:
        answer = _("Time is over.") + " " + data_uno.add_card(state.bot, message.entities[-1].user)
        await state.update_data(uno=data_uno.dict())

        poll_message = await message.answer_poll(
            _("Kick a player from the game?"),
            options=[_("Yes"), _("No, keep playing")],
        )

        from ..poll import close_poll_timer

        asyncio.create_task(
            close_poll_timer(poll_message, state, message.entities[-1].user),
            name=f'uno:{poll_message.poll.id}'
        )

        await asyncio.sleep(2)

        from .core import post

        await post(message, data_uno, state, answer)
