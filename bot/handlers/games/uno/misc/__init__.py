import asyncio
from random import choice

from aiogram import types
from aiogram.fsm.context import FSMContext
from aiogram.utils.i18n import gettext as _

from bot.utils.timer import timer
from .bot import UnoBot
from .cards import UnoCard, UnoEmoji, UnoColors
from .data import UnoData
from ..settings import UnoMode


async def timeout_proceed(message: types.Message, state: FSMContext):
    data_uno: UnoData = await UnoData.get_data(state)
    data_uno.timer_amount -= 1

    if not data_uno.timer_amount or len(data_uno.users) == 2:
        from ... import close_timeout
        await close_timeout(message, state)

        data_uno.settings.mode = UnoMode.FAST

        from .process import finish
        return await finish(state, data_uno)

    answer = _("Time is over.") + " " + data_uno.pick_card(message.entities[-1].user)
    await data_uno.set_data(state)

    poll_message = await message.answer_poll(
        _("Kick a player from the game?"),
        options=[_("Yes"), _("No, keep playing")],
    )

    task_poll = timer.create(
        state,
        coroutine_done=UnoBot.gen_poll,
        name='game:poll',
        message=poll_message,
        user=message.entities[-1].user,
    )

    await asyncio.sleep(2)

    if data_uno.current_card.color is UnoColors.BLACK:
        data_uno.current_card.color = choice(tuple(UnoColors.get_colors(exclude={UnoColors.BLACK})))
        await message.edit_text(_("Current color: {color}").format(color=data_uno.current_card.color.word))

        from .process import proceed_turn
        await proceed_turn(message, state, data_uno)

    else:
        from .process import next_turn
        await next_turn(message, state, data_uno, answer)

    await task_poll


async def timeout_finally(message: types.Message, state: FSMContext):
    task_name = timer.get_name(state, 'game')

    await timer.cancel(f"{task_name}:uno")
    await timer.cancel(f"{task_name}:poll")

    from . import keyboards as k

    if message.reply_markup and \
            message.reply_markup.inline_keyboard[0][0].callback_data == k.UnoKeyboard(action=k.UnoActions.BLUFF).pack():
        del message.reply_markup.inline_keyboard[0]
        await message.edit_reply_markup(message.reply_markup)
