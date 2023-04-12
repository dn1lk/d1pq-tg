from random import choice

from aiogram import types
from aiogram.fsm.context import FSMContext
from aiogram.utils.i18n import gettext as _

from bot.utils import TimerTasks
from .. import keyboards
from ..data import UnoData


async def update_uno(
        message: types.Message,
        state: FSMContext,
        timer: TimerTasks,
        data_uno: UnoData,
        user: types.User
):
    from .bot import UnoBot

    bot_uno = UnoBot(message, state, timer, data_uno)
    timer_uno = TimerTasks('say_uno')

    if data_uno.players[user.id].is_me:
        answer_uno = choice(
            (
                _("I have only one card!"),
                _("I am left with one card."),
                _("I am on the verge of victory!"),
                _("I hope no one finds out that I only have one card left...")
            )
        )

        timer_uno[state.key] = bot_uno.gen_uno(0, 4)
    else:
        answer_uno = choice(
            (
                _("{user} is left with one card!"),
                _("{user} is on the verge of victory!"),
                _("{user} has only one card and right now he can get +2 cards."),
                _("I want to note that the {user} has the last card left!"),
            )
        ).format(user=user.mention_html())

        timer_uno[state.key] = bot_uno.gen_uno(2, 6)

    await message.answer(answer_uno, reply_markup=keyboards.say_uno())


async def proceed_uno(message: types.Message, state: FSMContext, data_uno: UnoData, user: types.User):
    if data_uno.players[user.id].is_me:
        answer_one = choice(
            (
                _("I toss"),
                _("I give"),
                _("I throw"),
                _("I say UNO to"),
            )
        )
    else:
        answer_one = choice(
            (
                _("{user} tosses"),
                _("{user} gives"),
                _("{user} throws"),
                _("{user} carefully puts"),
            )
        ).format(user=user.mention_html())

    if message.entities:  # if user has one card
        uno_user = message.entities[0].user

        answer_two = _("player {uno_user}").format(uno_user=uno_user.mention_html())
    else:  # if bot has one card
        uno_user = await state.bot.me()

        answer_two = _("me")

    data_uno.players[uno_user.id].add_card(*data_uno.deck[2])
    await data_uno.set_data(state)

    answer_three = _("2 cards.")

    await message.edit_text(f'{answer_one} {answer_two} {answer_three}')
