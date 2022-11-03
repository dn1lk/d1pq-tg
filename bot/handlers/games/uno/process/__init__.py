import asyncio
from random import choice

from aiogram import types
from aiogram.fsm.context import FSMContext
from aiogram.utils.i18n import gettext as _

from .bot import UnoBot
from .cards import UnoCard, UnoEmoji, UnoColors
from .data import UnoData
from ..settings import UnoMode
from ... import keyboards as k


async def timeout(message: types.Message, state: FSMContext):
    data_uno: UnoData = await UnoData.get(state)
    data_uno.timer_amount -= 1

    if not data_uno.timer_amount or len(data_uno.users) == 2:
        from ... import close_timeout
        await close_timeout(message, state)

        data_uno.settings.mode = UnoMode.fast

        from .core import finish
        return await finish(state, data_uno)

    answer = _("Time is over.") + " " + data_uno.pick_card(message.entities[-1].user)
    await data_uno.update(state)

    poll_message = await message.answer_poll(
        _("Kick a player from the game?"),
        options=[_("Yes"), _("No, keep playing")],
    )

    bot_uno = UnoBot(poll_message, state, data_uno)
    asyncio.create_task(bot_uno.gen_poll(message.entities[-1].user), name=f'{bot_uno}:poll')

    await asyncio.sleep(2)

    if data_uno.current_card.color is UnoColors.black:
        data_uno.current_card.color = choice(tuple(UnoColors.get_colors(exclude={UnoColors.black})))
        await message.edit_text(_("Current color: {color}").format(color=data_uno.current_card.color.word))

        from .core import proceed_turn
        await proceed_turn(message, state, data_uno)

    else:
        from .core import post
        await post(message, state, data_uno, answer)


async def timeout_exception(message: types.Message, state: FSMContext):
    data_uno: UnoData = await UnoData.get(state)

    if data_uno.current_state.bluffed:
        await message.edit_reply_markup(k.uno_show_cards(0))
