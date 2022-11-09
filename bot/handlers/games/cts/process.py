from random import choice

from aiogram import Router, types
from aiogram.fsm.context import FSMContext
from aiogram.utils.i18n import gettext as _

from bot.utils.timer import timer
from .misc.data import CTSData
from .. import WINNER, Games, win_timeout

router = Router(name='game:cts:process')
router.message.filter(Games.CTS)


@router.message(CTSData.filter())
async def answer_handler(message: types.Message, state: FSMContext):
    await timer.cancel(timer.get_name(state, name='game'))
    data_cts = await CTSData.get_data(state)

    if data_cts.bot_var:
        message = await message.reply(
            choice(
                (
                    _("Hmm."),
                    _("And you're smarter than you look."),
                    _("Right!"),
                )
            ) + _(" My word: {bot_var}.").format(bot_var=data_cts.bot_var)
        )

        await data_cts.set_data(state)
        await timer.create(state, win_timeout, name='game', message=message)
    else:
        await state.clear()

        await message.reply(choice(
            (
                _("Okay, I have nothing to write on {letter}... Victory is yours."),
                _("Can't find the right something on {letter}... My defeat."),
                _("VICTORY... yours. I can't remember that name... You know, it also starts with {letter}..."),
            )
        ).format(letter=f'"{message.text[-1]}"'))


@router.message()
async def mistake_handler(message: types.Message, state: FSMContext):
    data_cts = await CTSData.get_data(state)
    data_cts.fail_amount -= 1

    if data_cts.fail_amount:
        await data_cts.set_data(state)

        if message.text in data_cts.cities:
            answer = (
                _("We have already used this name. Choose another!"),
                _("I remember exactly that we already used this. Let's try something else."),
                _("But no, you can’t fool me - this name was already in the game. Be original!")
            )
        else:
            answer = (
                _("I do not understand something or your word is WRONG!"),
                _("And here it is not. Think better, user!"),
                _("My algorithms do not deceive me - you are mistaken!"),
            )

        end = _("\n<b>Remaining attempts</b>: {fail_amount}").format(fail_amount=data_cts.fail_amount)

    else:
        await timer.cancel(timer.get_name(state, name='game'))
        await state.clear()

        answer = (
            _("You have no attempts left."),
            _("Looks like all attempts have been spent."),
            _("Where is an ordinary user up to artificial intelligence. All attempts have ended."),
        )

        end = str(choice(WINNER)) + _("\n<b>Words guessed</b>: {words}.").format(words=len(data_cts.cities))

    await message.reply(f'{choice(answer)} {end}')
