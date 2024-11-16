import asyncio
import contextlib
import logging
import secrets
from dataclasses import replace
from typing import cast

from aiogram import Bot, exceptions, types
from aiogram.fsm.context import FSMContext
from aiogram.utils import formatting
from aiogram.utils.i18n import gettext as _

from handlers.commands.play import CLOSE
from handlers.commands.play.uno import MIN_PLAYERS
from handlers.commands.play.uno.misc.data.base import UnoData, UnoState
from handlers.commands.play.uno.misc.data.deck.colors import UnoColors
from utils import TimerTasks

from .bot import UnoBot

logger = logging.getLogger("bot.uno")


async def _timeout(message: types.Message, bot: Bot, state: FSMContext, timer: TimerTasks) -> None:
    data_uno = await UnoData.get_data(state)
    if data_uno is None:
        return

    logger.debug("[UNO] timeout executing: %s", data_uno)
    data_uno.timer_amount -= 1

    if not data_uno.timer_amount or len(data_uno.players) == MIN_PLAYERS:
        content = formatting.Text(secrets.choice(CLOSE))
        await message.reply(**content.as_kwargs())

        for player_id, player_data in data_uno.players.playing.items():
            if player_data.points:
                data_uno.players.finished[player_id] = player_data

        from .base import finish

        await finish(bot, state, timer, data_uno)

    else:
        content = formatting.Text(_("Kick a player from the game?"))
        message_poll = await message.answer_poll(
            options=[_("Yes"), _("No, keep playing")],
            **content.as_kwargs(
                text_key="question",
                entities_key="question_entities",
                parse_mode_key="question_parse_mode",
            ),
        )

        player_id = data_uno.players.current_id
        last_card = data_uno.deck.last_card

        bot_poll = UnoBot(message_poll, bot, state, data_uno)

        key = replace(state.key, destiny="play:uno:poll")
        timer[key] = bot_poll.gen_poll(timer, player_id)

        await asyncio.sleep(2)

        user = await data_uno.players.get_user(bot, state.key.chat_id, player_id)
        if last_card.color is UnoColors.BLACK:
            color = secrets.choice(tuple(UnoColors.exclude(UnoColors.BLACK)))
            color = cast(UnoColors, color)
            data_uno.do_color(user, color)

            content = formatting.Text(_("Ok, current color: {color}").format(color=color))
        else:
            content = formatting.Text(_("Time is over."), " ", data_uno.pick_card(user))

        # Reset states
        data_uno.state = UnoState()

        from .turn import next_turn

        await next_turn(message, bot, state, timer, data_uno, content)


async def _finally(message: types.Message, state: FSMContext, timer: TimerTasks) -> None:
    key = replace(state.key, destiny="play:uno:last")
    del timer[key]

    if message.reply_markup and len(message.reply_markup.inline_keyboard) == 2:
        del message.reply_markup.inline_keyboard[0]

        # TODO: remove exception
        with contextlib.suppress(exceptions.TelegramBadRequest):
            await message.edit_reply_markup(reply_markup=message.reply_markup)


async def task(
    message: types.Message,
    bot: Bot,
    state: FSMContext,
    timer: TimerTasks,
    data_uno: UnoData,
) -> None:
    try:
        await asyncio.sleep(60 * data_uno.timer_amount)

        async with timer.lock(state.key):
            await _timeout(message, bot, state, timer)
    finally:
        await _finally(message, state, timer)


def clear(state: FSMContext, timer: TimerTasks) -> None:
    del timer[state.key]

    for destiny in ("play:uno:last", "play:uno:poll"):
        key = replace(state.key, destiny=destiny)
        del timer[key]
