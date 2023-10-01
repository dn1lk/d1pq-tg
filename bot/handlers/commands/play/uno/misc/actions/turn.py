import asyncio
from dataclasses import replace
from random import choice

from aiogram import Bot, types, exceptions
from aiogram.fsm.context import FSMContext
from aiogram.utils.i18n import gettext as _

from core.utils import TimerTasks
from .bot import UnoBot
from .. import errors, keyboards
from ..data import UnoData
from ..data.deck import UnoCard
from ..data.settings.modes import UnoMode


async def proceed_turn(
        message: types.Message,
        bot: Bot,
        state: FSMContext,
        timer: TimerTasks,
        data_uno: UnoData,
        card: UnoCard,
        answer: str,
):
    try:
        user = message.from_user

        try:
            data_uno.update_turn(user.id, card)

        except errors.UnoOneCard:
            from .uno import update_uno
            await update_uno(message, bot, state, timer, data_uno)

        except errors.UnoNoCards:
            from .kick import kick_for_cards
            await kick_for_cards(bot, state, data_uno, user)

            if (
                    data_uno.settings.mode is UnoMode.FAST and len(data_uno.players.playing) == 1
                    or max(player.points for player in data_uno.players.finished.values()) >= 500
            ):
                raise errors.UnoFinish()
            else:
                raise errors.UnoRestart()

    except errors.UnoFinish:
        from .base import finish
        await finish(bot, state, timer, data_uno)

    except errors.UnoRestart:
        from .base import restart
        await restart(bot, state, timer, data_uno)

    else:
        await proceed_state(message, bot, state, timer, data_uno, answer)


async def proceed_state(
        message: types.Message,
        bot: Bot,
        state: FSMContext,
        timer: TimerTasks,
        data_uno: UnoData,
        answer: str,
):
    try:
        answer = data_uno.update_state() or answer

    except errors.UnoSeven:
        if data_uno.players.current_data.is_me:
            bot_uno = UnoBot(message, bot, state, data_uno)
            answer = await bot_uno.do_seven()
        else:
            await _proceed_seven(message, bot, state, timer, data_uno)
            return

    except errors.UnoColor:
        if data_uno.players.current_data.is_me:
            bot_uno = UnoBot(message, bot, state, data_uno)
            answer = await bot_uno.do_color()
        else:
            await _proceed_color(message, bot, state, timer, data_uno)
            return

    await next_turn(message, bot, state, timer, data_uno, answer)


async def _proceed_seven(
        message: types.Message,
        bot: Bot,
        state: FSMContext,
        timer: TimerTasks,
        data_uno: UnoData,
):
    await data_uno.set_data(state)

    answer = _(
        "{user}, with whom will you exchange cards?\n"
        "Mention (@) this player in your next message."
    ).format(user=message.from_user.mention_html())

    message = await message.answer(answer)
    await update_timer(message, bot, state, timer, data_uno)


async def _proceed_color(
        message: types.Message,
        bot: Bot,
        state: FSMContext,
        timer: TimerTasks,
        data_uno: UnoData,
):
    await data_uno.set_data(state)

    answer = choice(
        (
            _("Finally, we will change the color.\nWhat will {user} choose?"),
            _("New color, new light.\nby {user}."),
        )
    ).format(user=message.from_user.mention_html())

    message = await message.answer(answer, reply_markup=keyboards.choice_color())
    await update_timer(message, bot, state, timer, data_uno)


async def next_turn(
        message: types.Message,
        bot: Bot,
        state: FSMContext,
        timer: TimerTasks,
        data_uno: UnoData,
        answer: str
):
    current_id = data_uno.players.current_id
    user = message.from_user

    if user.id != current_id:  # for skipped
        user = await data_uno.players.get_user(bot, state.key.chat_id, current_id)

    answer = answer.format(user=user.mention_html())
    answer_next = await data_uno.do_next(bot, state)

    try:
        message = await message.reply(f'{answer}\n{answer_next}',
                                      reply_markup=keyboards.show_cards(bluffed=data_uno.state.bluffed))
    except exceptions.TelegramRetryAfter as retry:
        await asyncio.sleep(retry.retry_after)
        message = await retry.method

    await update_timer(message, bot, state, timer, data_uno)


async def update_timer(
        message: types.Message,
        bot: Bot,
        state: FSMContext,
        timer: TimerTasks,
        data_uno: UnoData,
):
    from .bot import UnoBot
    bot_uno = UnoBot(message, bot, state, data_uno)
    cards = tuple(bot_uno.get_cards())

    if cards or data_uno.players.current_data.is_me:
        # Run bot turn

        timer[state.key] = bot_uno.gen_turn(timer, *cards)

    from .timer import task
    timer[state.key] = task(message, bot, state, timer, data_uno)
