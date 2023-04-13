from random import choice

from aiogram import types
from aiogram.fsm.context import FSMContext
from aiogram.utils.i18n import gettext as _

from bot.core.utils import TimerTasks
from .bot import UnoBot
from .. import errors, keyboards
from ..data import UnoData
from ..data.deck import UnoCard, UnoEmoji


async def proceed_turn(
        message: types.Message,
        state: FSMContext,
        timer: TimerTasks,
        data_uno: UnoData,
        card: UnoCard,
        answer: str,
):
    try:
        user = message.from_user

        try:
            await data_uno.update_turn(state, user.id, card)

        except errors.UnoOneCard:
            from .uno import update_uno
            await update_uno(message, state, timer, data_uno, user)

        except errors.UnoNoCards:
            from .kick import kick_for_cards
            await kick_for_cards(state, data_uno, user)

    except errors.UnoRestart:
        data_uno.restart()

        from .base import restart
        await restart(state, timer, data_uno)

    except errors.UnoEnd:
        from .base import finish
        await finish(state, timer, data_uno)

    else:
        await proceed_action(message, state, timer, data_uno, answer)


async def proceed_action(
        message: types.Message,
        state: FSMContext,
        timer: TimerTasks,
        data_uno: UnoData,
        answer: str,
):
    try:
        answer_action = data_uno.update_action()

        user = await data_uno.players.current_player.get_user(state.bot, state.key.chat_id)
        answer = (answer_action or answer).format(user=user.mention_html())

    except errors.UnoSeven:
        if data_uno.players.current_player.is_me:
            bot_uno = UnoBot(message, state, timer, data_uno)
            answer = await bot_uno.do_seven()
        else:
            await proceed_seven(state, timer, data_uno)
            return

    except errors.UnoColor:
        if data_uno.players.current_player.is_me:
            bot_uno = UnoBot(message, state, timer, data_uno)
            answer = await bot_uno.do_color()

            data_uno.update_action()
        else:
            await proceed_color(state, timer, data_uno)
            return

    await next_turn(message, state, timer, data_uno, answer)


async def proceed_seven(
        state: FSMContext,
        timer: TimerTasks,
        data_uno: UnoData,
):
    await data_uno.set_data(state)
    user = await data_uno.players.current_player.get_user(state.bot, state.key.chat_id)

    answer = _(
        "{user}, with whom will you exchange cards?\n"
        "Mention (@) this player in your next message."
    ).format(user=user.mention_html())

    message = await state.bot.send_message(
        state.key.chat_id,
        answer,
    )

    await update_timer(message, state, timer, data_uno)


async def proceed_color(
        state: FSMContext,
        timer: TimerTasks,
        data_uno: UnoData,
):
    await data_uno.set_data(state)
    user = await data_uno.players.current_player.get_user(state.bot, state.key.chat_id)

    answer = choice(
        (
            _("Finally, we will change the color.\nWhat will {user} choose?"),
            _("New color, new light.\nby {user}."),
        )
    ).format(user=user.mention_html())

    message = await state.bot.send_message(
        state.key.chat_id,
        answer,
        reply_markup=keyboards.choice_color(),
    )

    await update_timer(message, state, timer, data_uno)


async def next_turn(
        message: types.Message,
        state: FSMContext,
        timer: TimerTasks,
        data_uno: UnoData,
        answer: str
):
    answer_next = await data_uno.do_next(state)
    is_draw_four = data_uno.actions.drawn and data_uno.deck.last_card.emoji is UnoEmoji.DRAW_FOUR

    message = await message.reply(f'{answer}\n{answer_next}',
                                  reply_markup=keyboards.show_cards(is_draw_four))

    await update_timer(message, state, timer, data_uno)


async def update_timer(
        message: types.Message,
        state: FSMContext,
        timer: TimerTasks,
        data_uno: UnoData,
):
    from .bot import UnoBot
    bot_uno = UnoBot(message, state, timer, data_uno)
    cards = tuple(bot_uno.get_cards())

    if cards or data_uno.players.current_player.is_me:
        timer[state.key] = bot_uno.gen_turn(cards)

    from .timer import task
    timer[state.key] = task(message, state, timer, data_uno)
