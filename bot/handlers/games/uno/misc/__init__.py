import asyncio
from random import choice

from aiogram import types
from aiogram.fsm.context import FSMContext
from aiogram.utils.i18n import gettext as _

from bot.utils.timer import Timer
from . import keyboards as k
from .bot import UnoBot
from .cards import UnoCard, UnoEmoji, UnoColors
from .data import UnoData
from ..settings import UnoMode


async def timeout(message: types.Message, state: FSMContext, timer: Timer):
    data_uno: UnoData = await UnoData.get_data(state)
    data_uno.timer_amount -= 1

    if not data_uno.timer_amount or len(data_uno.users) == 2:
        from ... import close_timeout
        await close_timeout(message, state)

        data_uno.settings.mode = UnoMode.fast

        from .process import finish
        return await finish(state, timer, data_uno)

    answer = _("Time is over.") + " " + data_uno.pick_card(message.entities[-1].user)
    await data_uno.set_data(state)

    poll_message = await message.answer_poll(
        _("Kick a player from the game?"),
        options=[_("Yes"), _("No, keep playing")],
    )

    timer[timer.get_name(state, 'game:poll')] = asyncio.create_task(
        UnoBot.gen_poll(
            poll_message,
            state,
            timer,
            message.entities[-1].user,
        )
    )

    await asyncio.sleep(2)

    if data_uno.current_card.color is UnoColors.black:
        data_uno.current_card.color = choice(tuple(UnoColors.get_colors(exclude={UnoColors.black})))
        await message.edit_text(_("Current color: {color}").format(color=data_uno.current_card.color.word))

        from .process import proceed_turn
        await proceed_turn(message, state, timer, data_uno)

    else:
        from .process import next_turn
        await next_turn(message, state, timer, data_uno, answer)


async def timeout_done(message: types.Message, state: FSMContext, timer: Timer):
    task_name = timer.get_name(state, 'game')

    await timer.cancel(f"{task_name}:uno")
    await timer.cancel(f"{task_name}:poll")

    if message.reply_markup and \
            message.reply_markup.inline_keyboard[0][0].callback_data == k.UnoKeyboard(action='bluff').pack():
        await message.edit_reply_markup(k.show_cards(0))
