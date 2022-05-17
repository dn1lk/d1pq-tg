from asyncio import sleep
from random import choice
from typing import Union, Optional

from aiogram import Bot, Router, types
from aiogram.dispatcher.fsm.context import FSMContext
from aiogram.utils.chat_action import ChatActionSender
from aiogram.utils.i18n import I18n, gettext as _

from worker import filters as f
from worker.handlers.games import GameState, get_game_cts

router = Router(name='game_cts')
router.message.filter(state=GameState.CTS)


def get_game_cts_win() -> str:
    return choice(
        (
            _("Victory for me."),
            _("I am a winner."),
            _("I am the winner in this game."),
        )
    )


async def game_cts_filter(message: types.Message, state: FSMContext, i18n: I18n) -> Union[dict, bool]:
    def get() -> str:
        for city in game_vars:
            if city[0].lower() == message.text[-1].lower() and city not in cities:
                yield city

    async with ChatActionSender.typing(chat_id=message.chat.id):
        bot_var, cities, failed = (await state.get_data())['game_cts']

        if not bot_var or message.text[0].lower() == bot_var[-1].lower():
            game_vars = get_game_cts(i18n.current_locale)

            if message.text not in cities:
                if await f.LevenshteinFilter(
                        lev=[game_var for game_var in game_vars if game_var[0].lower() == message.text[0].lower()]
                )(obj=message):
                    cities.append(message.text)

                    bot_var = choice(list(get())[::choice(range(1, 11))] + [None])

                    await state.update_data({'game_cts': (bot_var, cities, failed)})
                    return {'bot_var': bot_var}

        return False


@router.message(game_cts_filter)
async def game_cts_two_yes_handler(message: types.Message, bot: Bot, state: FSMContext, bot_var: Optional[str] = None):
    async def timer(answer):
        await sleep(60)

        data_new = (await state.get_data()).get('game_cts')

        if data_new and bot_var == data_new[0]:
            await bot.send_message(
                chat_id=message.chat.id,
                text=_("Your time is up. ") + get_game_cts_win(),
                reply_to_message_id=answer.message_id
            )
            await state.clear()

    if bot_var:
        await timer(
            await message.reply(
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
        )
    else:
        await message.reply(choice(
            (
                _("Okay, I have nothing to write on {letter}... Victory is yours."),
                _("Can't find the right title on {letter}... My defeat."),
                _("VICTORY... yours. I can't remember that name... You know, it also starts with {letter}..."),
            )
        ).format(letter=f'"{message.text[-1]}"'))
        await state.clear()


@router.message()
async def game_cts_two_no_handler(message: types.Message, state: FSMContext):
    bot_var, cities, failed = (await state.get_data())['game_cts']

    if failed - 1 > 0:
        end = _("\nRemaining attempts: {failed}").format(failed=failed - 1)

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

        await state.update_data({'game_cts': (bot_var, cities, failed - 1)})
    else:
        end = get_game_cts_win()
        answer = (
            _("You have no attempts left. "),
            _("Looks like all attempts have been spent. "),
            _("Where is an ordinary user up to artificial intelligence. All attempts have ended. "),
        )

        await state.clear()

    await message.reply(choice(answer) + end)
