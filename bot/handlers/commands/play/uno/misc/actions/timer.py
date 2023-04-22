import asyncio
from random import choice

from aiogram import Bot, types
from aiogram.fsm.context import FSMContext
from aiogram.utils.i18n import gettext as _

from bot.core.utils import TimerTasks
from bot.handlers.commands.play import CLOSE
from .bot import UnoBot
from ..data.base import UnoData, UnoState
from ..data.deck.colors import UnoColors


async def _timeout(message: types.Message, bot: Bot, state: FSMContext, timer: TimerTasks):
    data_uno = await UnoData.get_data(state)
    data_uno.timer_amount -= 1

    if not data_uno.timer_amount or len(data_uno.players) == 2:
        answer = choice(CLOSE).value
        await message.reply(answer)

        for player_id, player_data in data_uno.players.playing.items():
            if player_data.points:
                data_uno.players.finished[player_id] = player_data

        from .base import finish
        await finish(bot, state, timer, data_uno)

    else:
        message_poll = await message.answer_poll(
            _("Kick a player from the game?"),
            options=[_("Yes"), _("No, keep playing")],
        )

        player_id = data_uno.players.current_id
        last_card = data_uno.deck.last_card

        bot_poll = UnoBot(message_poll, bot, state, data_uno)

        timer_poll = TimerTasks('uno_poll')
        timer_poll[state.key] = bot_poll.gen_poll(timer, player_id)

        await asyncio.sleep(2)

        if last_card.color is UnoColors.BLACK:
            color = choice(tuple(UnoColors.exclude(UnoColors.BLACK)))
            data_uno.do_color(color)

            answer = _("Ok, current color: {color}").format(color=color)

        else:
            user = await data_uno.players.get_user(bot, state.key.chat_id, player_id)
            answer = f'{_("Time is over.")} {data_uno.pick_card(user)}'

        # Reset states
        data_uno.state = UnoState()

        from .turn import next_turn
        await next_turn(message, bot, state, timer, data_uno, answer)


async def _finally(message: types.Message, state: FSMContext):
    timer_uno = TimerTasks('say_uno')
    del timer_uno[state.key]

    if message.reply_markup and len(message.reply_markup.inline_keyboard) == 2:
        del message.reply_markup.inline_keyboard[0]
        await message.edit_reply_markup(reply_markup=message.reply_markup)


async def task(
        message: types.Message,
        bot: Bot,
        state: FSMContext,
        timer: TimerTasks,
        data_uno: UnoData
):
    try:
        await asyncio.sleep(60 * data_uno.timer_amount)

        async with timer.lock(state.key):
            await _timeout(message, bot, state, timer)
    finally:
        await _finally(message, state)


def clear(state: FSMContext, timer: TimerTasks):
    del timer[state.key]

    timer_poll = TimerTasks('uno_poll')
    del timer_poll[state.key]
