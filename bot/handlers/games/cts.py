from random import choice
from typing import Union

from aiogram import Router, types
from aiogram.dispatcher.fsm.context import FSMContext
from aiogram.utils.chat_action import ChatActionSender
from aiogram.utils.i18n import I18n, gettext as _

from bot import filters as f
from . import Game, WINNER, get_cts, timer, win_timeout

router = Router(name='game:cts')
router.message.filter(Game.cts)


async def game_cts_filter(message: types.Message, state: FSMContext, i18n: I18n) -> Union[dict, bool]:
    def get() -> str:
        for city in game_vars:
            if city[0].lower() == message.text[-1].lower() and city not in cities:
                yield city

    async with ChatActionSender.typing(chat_id=message.chat.id):
        data = await state.get_data()
        bot_var, cities, failed = data['cts']

        if not bot_var or message.text[0].lower() == bot_var[-1].lower():
            game_vars = get_cts(i18n.current_locale)

            if message.text not in cities:
                if await f.LevenshteinFilter(
                        lev=set(filter(lambda game_var: game_var[0].lower() == message.text[0].lower(), game_vars))
                )(obj=message):
                    cities.append(message.text)

                    data['cts'] = (choice(list(get())[::choice(range(1, 11))] + [None]), cities, failed)

                    await state.set_data(data)
                    return {'data': data}


@router.message(game_cts_filter)
async def game_cts_answer_yes_handler(
        message: types.Message,
        state: FSMContext,
        data: dict
):
    bot_var, cities, failed = data.pop('cts')

    if bot_var:
        message = await message.reply(
            (
                choice(
                    (
                        _("Hmm."),
                        _("And you're smarter than you look."),
                        _("Right!"),
                    )
                )
            ) + _(" My word: {bot_var}.").format(bot_var=bot_var)
        )

        timer(state, win_timeout, message=message)
    else:
        await message.reply(choice(
            (
                _("Okay, I have nothing to write on {letter}... Victory is yours."),
                _("Can't find the right title on {letter}... My defeat."),
                _("VICTORY... yours. I can't remember that name... You know, it also starts with {letter}..."),
            )
        ).format(letter=f'"{message.text[-1]}"'))

        await state.set_state()
        await state.set_data(data)


@router.message()
async def game_cts_two_no_handler(message: types.Message, state: FSMContext):
    data = await state.get_data()
    bot_var, cities, failed = data['cts']

    if failed - 1 > 0:
        end = _("\n\nRemaining attempts: {failed}").format(failed=failed - 1)

        if message.text in cities:
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

        await state.update_data(cts=(bot_var, cities, failed - 1))
    else:
        end = str(choice(WINNER))
        answer = (
            _("You have no attempts left. "),
            _("Looks like all attempts have been spent. "),
            _("Where is an ordinary user up to artificial intelligence. All attempts have ended. "),
        )

        await state.set_state()
        await state.set_data(data)

    await message.reply(choice(answer) + end)
