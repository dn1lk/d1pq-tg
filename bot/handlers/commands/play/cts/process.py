from random import choice

from aiogram import Router, types, flags, html
from aiogram.fsm.context import FSMContext
from aiogram.utils.i18n import gettext as _

from bot.core.utils import TimerTasks
from . import CTSData, task
from .. import PlayStates

router = Router(name='play:cts:process')
router.message.filter(PlayStates.CTS)


async def finish(message: types.Message, state: FSMContext, data_cts: CTSData, answer_one: str):
    await state.clear()

    answer_two = _("<b>Cities guessed</b>: {cities}.").format(cities=len(data_cts.used_cities))
    await message.reply(f"{answer_one}\n{answer_two}")


@router.message(CTSData.filter())
@flags.timer('play')
async def answer_handler(message: types.Message, state: FSMContext, data_cts: CTSData, timer: TimerTasks):
    if data_cts.bot_city:
        answer_one = choice(
            (
                _("Hmm."),
                _("And you're smarter than you look."),
                _("Right!"),
            )
        )

        answer_two = _("My word: {bot_city}.").format(bot_city=data_cts.bot_city)
        message = await message.reply(f"{answer_one} {answer_two}")

        await data_cts.set_data(state)
        timer[state.key] = task(message, state)
    else:
        answer = choice(
            (
                _("Okay, I have nothing to write on {letter}... Victory is yours."),
                _("Can't find the right something on {letter}... My defeat."),
                _("VICTORY... yours. I can't remember that name... You know, it also starts with {letter}..."),
            )
        ).format(letter=html.bold(f'"{message.text[-1]}"'))

        await finish(message, state, data_cts, answer)


@router.message()
@flags.timer(name='play', cancelled=False)
async def mistake_handler(message: types.Message, state: FSMContext, timer: TimerTasks):
    data_cts = await CTSData.get_data(state)
    data_cts.fail_amount -= 1

    if data_cts.fail_amount:
        await data_cts.set_data(state)

        if message.text in data_cts.used_cities:
            answer_one = choice(
                (
                    _("We have already used this name. Choose another!"),
                    _("I remember exactly that we already used this. Let's try something else."),
                    _("But no, you can’t fool me - this name was already in the game. Be original!")
                )
            )
        else:
            answer_one = choice(
                (
                    _("I do not understand something or your word is WRONG!"),
                    _("And here it is not. Think better, user!"),
                    _("My algorithms do not deceive me - you are mistaken!"),
                )
            )

        answer_two = _("<b>Remaining attempts</b>: {fail_amount}").format(fail_amount=data_cts.fail_amount)
        await message.reply(f"{answer_one}\n{answer_two}")

    else:
        del timer[state.key]

        answer = choice(
            (
                _("You have no attempts left."),
                _("Looks like all attempts have been spent."),
                _("Where is an ordinary user up to artificial intelligence. All attempts have ended."),
            )
        )

        await finish(message, state, data_cts, answer)
