from random import choice

from aiogram import Bot, types
from aiogram.fsm.context import FSMContext
from aiogram.utils.i18n import gettext as _

from bot.core.utils import TimerTasks
from .. import keyboards
from ..data import UnoData


async def update_uno(
        message: types.Message,
        bot: Bot,
        state: FSMContext,
        data_uno: UnoData,
):
    user = message.from_user

    if data_uno.players[user.id].is_me:
        a, b = 0, 4

        answer = choice(
            (
                _("I have only one card!"),
                _("I am left with one card."),
                _("I am on the verge of victory!"),
                _("This is my penultimate card...")
            )
        )

    else:
        a, b = 2, 6

        answer = choice(
            (
                _("{user} is left with one card!"),
                _("{user} is on the verge of victory!"),
                _("{user} can get +2 cards right now."),
                _("I want to note — {user} has the last card left!"),
            )
        ).format(user=user.mention_html())

    message = await message.answer(answer, reply_markup=keyboards.say_uno())

    from .bot import UnoBot
    bot_uno = UnoBot(message, bot, state, data_uno)

    timer_uno = TimerTasks('say_uno')
    timer_uno[state.key] = bot_uno.gen_uno(a, b)


async def proceed_uno(
        message: types.Message,
        bot: Bot,
        state: FSMContext,
        data_uno: UnoData,
        user: types.User,
):
    if data_uno.players[user.id].is_me:
        answer_one = choice(
            (
                _("I toss 2 cards"),
                _("I give 2 cards"),
                _("I throw 2 cards"),
                _("I say UNO"),
            )
        )
    else:
        answer_one = choice(
            (
                _("{user} tosses 2 cards"),
                _("{user} gives 2 cards"),
                _("{user} throws 2 cards"),
                _("{user} say UNO"),
            )
        ).format(user=user.mention_html())

    if message.entities:  # if user has one card
        uno_user = message.entities[-1].user
        answer_two = _("to {uno_user}").format(uno_user=uno_user.mention_html())
    else:  # if bot has one card
        uno_user = await bot.me()
        answer_two = choice(
            (
                _("to me"),
                _("to your servitor"),
            )
        )

    data_uno.players.playing[uno_user.id].add_card(*data_uno.deck(2))
    await data_uno.set_data(state)

    await message.edit_text(f'{answer_one} {answer_two}.')
