import asyncio
from random import choice

from aiogram import types
from aiogram.fsm.context import FSMContext
from aiogram.utils.i18n import gettext as _

from bot.core.utils import TimerTasks
from bot.handlers.commands.play import CLOSE
from .bot import UnoBot
from ..data import UnoData
from ..data.deck.colors import UnoColors
from ..data.settings.modes import UnoMode


async def _timeout(message: types.Message, state: FSMContext, timer: TimerTasks):
    data_uno = await UnoData.get_data(state)
    data_uno.timer_amount -= 1

    if not data_uno.timer_amount or len(data_uno.players) == 2:
        data_uno.settings.mode = UnoMode.FAST
        await data_uno.players.kick_player(state, data_uno.deck, data_uno.players.current_player)

        answer = choice(CLOSE).value
        await message.reply(answer)

        from .base import finish
        await finish(state, timer, data_uno)

    else:
        message_poll = await message.answer_poll(
            _("Kick a player from the game?"),
            options=[_("Yes"), _("No, keep playing")],
        )

        bot_poll = UnoBot(message_poll, state, timer, data_uno)

        timer_poll = TimerTasks('uno_poll')
        timer_poll[state.key] = bot_poll.gen_poll()

        await asyncio.sleep(2)

        last_card = data_uno.deck.last_card

        if last_card.color is UnoColors.BLACK:
            color = choice(tuple(UnoColors.exclude(UnoColors.BLACK)))
            data_uno.deck[-1] = last_card.replace(color=color)

            answer = _("Current color: {color}").format(color=color)

        else:
            answer = f'{_("Time is over.")} {await data_uno.pick_card(state)}'

        from .turn import next_turn
        await next_turn(message, state, timer, data_uno, answer)


async def _finally(message: types.Message, state: FSMContext):
    timer_uno = TimerTasks('say_uno')
    del timer_uno[state.key]

    if message.reply_markup and len(message.reply_markup.inline_keyboard) == 2:
        del message.reply_markup.inline_keyboard[0]
        await message.edit_reply_markup(reply_markup=message.reply_markup)


async def task(
        message: types.Message,
        state: FSMContext,
        timer: TimerTasks,
        data_uno: UnoData
):
    try:
        await asyncio.sleep(60 * data_uno.timer_amount)
        await _timeout(message, state, timer)
    finally:
        await _finally(message, state)
