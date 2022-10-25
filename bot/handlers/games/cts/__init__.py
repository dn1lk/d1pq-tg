from random import choice

from aiogram import Router, types
from aiogram.fsm.context import FSMContext
from aiogram.utils.chat_action import ChatActionSender
from aiogram.utils.i18n import I18n, gettext as _

from .data import CtsData
from .. import Games, WINNER, timer, win_timeout

__all__ = 'router'

router = Router(name='game:cts')
router.message.filter(Games.cts)


async def game_cts_filter(message: types.Message, state: FSMContext, i18n: I18n) -> dict | bool:
    async with ChatActionSender.typing(chat_id=message.chat.id):
        data_cts = CtsData(**(await state.get_data())['cts'])

        if data_cts.filter_city(i18n.current_locale, message.text):
            return {'data_cts': data_cts}


@router.message(game_cts_filter)
async def answer_yes_handler(message: types.Message, state: FSMContext, data_cts: CtsData):
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

        await state.update_data(cts=data_cts.dict())
        timer(state, win_timeout, message=message)
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
async def answer_no_handler(message: types.Message, state: FSMContext):
    data_cts = CtsData(**(await state.get_data())['cts'])
    data_cts.fail_amount -= 1

    if data_cts.fail_amount:
        await state.update_data(cts=data_cts.dict())

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
        await state.clear()

        answer = (
            _("You have no attempts left."),
            _("Looks like all attempts have been spent."),
            _("Where is an ordinary user up to artificial intelligence. All attempts have ended."),
        )

        end = str(choice(WINNER)) + _("\n<b>Number of words guessed</b>: {words}.").format(words=len(data_cts.cities))

    await message.reply(f'{choice(answer)} {end}')
