from asyncio import sleep
from random import choice

from aiogram import Router, Bot, F, types, flags
from aiogram.dispatcher.fsm.context import FSMContext
from aiogram.utils.chat_action import ChatActionSender
from aiogram.utils.i18n import I18n, gettext as _

from worker import keyboards as k
from worker.handlers import USERNAME
from worker.handlers.games import GameState, game_timer, get_game_cts

router = Router(name='game_start')
router.message.filter(commands=['play', 'поиграем'], commands_ignore_case=True)


@router.message(F.text.lower().endswith(('cts', 'грд')))
async def game_cts_one_handler(message: types.Message, state: FSMContext, i18n: I18n):
    message = await message.answer(
        _(
            "Oh, the game of cities. Well, let's try!\n\n"
            "The rules are as follows: you need to answer the name of the settlement, "
            "starting with the last letter of the name of the previous settlement.\n"
            "You have 60 seconds to think."
        )
    )

    if choice(['bot_var', 'user_var']) == 'bot_var':
        bot_var = choice(get_game_cts(i18n.current_locale))
        answer = _("I start! My word: {bot_var}.").format(bot_var=bot_var)
    else:
        bot_var = None
        answer = _("You start! Your word?")

    await state.set_state(GameState.CTS)
    await state.update_data({'game_cts': (bot_var, [bot_var], 5)})

    await message.answer(answer)

    await game_timer(message, state)


@router.message(F.text.lower().endswith(('rnd', 'рнд')))
@flags.data('stickers')
async def game_rnd_one_handler(message: types.Message, bot: Bot, state: FSMContext, stickers: list):
    await message.answer(
        _(
            "Mm, {username} is trying his luck... Well, EVERYONE, EVERYONE, EVERYONE, pay attention!\n\n"
            "Enter any number between 1 and 10 and I'll choose "
            "my own in 60 seconds and we'll we'll see which one of you is right."
        ).format(
            username=USERNAME.format(
                id=message.from_user.id,
                name=message.from_user.first_name
            )
        )
    )

    async with ChatActionSender.typing(chat_id=message.chat.id, interval=2):
        await sleep(2)

        await state.set_state(state=GameState.RND)
        await bot.send_message(message.chat.id, _("LET THE BATTLE BEGIN!"))

    async with ChatActionSender.choose_sticker(chat_id=message.chat.id, interval=10):
        await sleep(60)

        stickers = sum(
            [(await bot.get_sticker_set(sticker_set)).stickers for sticker_set in stickers + ['TextAnimated']],
            []
        )
        await bot.send_sticker(
            message.chat.id,
            choice([sticker.file_id for sticker in stickers if sticker.emoji in ('⏳', '🙈')])
        )

    bot_var = str(choice(range(1, 11)))

    user_vars = (await state.get_data()).get('game_rnd')
    winners = [
        USERNAME.format(
            id=int(user_id),
            name=value[0]
        ) for user_id, value in user_vars.items() if value[1] == bot_var
    ] if user_vars else None

    await bot.send_message(message.chat.id, _("So my number is {bot}. Who guessed? Hmm...").format(bot=bot_var))

    if winners:
        answer = _("Well... the title of winner goes to: {winners}. Congratulations!").format(
            winners=", ".join(winners)
        )
    else:
        answer = _("Well... no one guessed right. Heh.")

    await bot.send_message(message.chat.id, answer)
    await state.clear()


@router.message(F.text.lower().endswith(('rps', 'кнб')))
async def game_rps_one_handler(message: types.Message, state: FSMContext):
    await state.set_state(state=GameState.RPS)
    await state.update_data({'game_rps': (0, 0)})

    await message.answer(_("Eh, classic. Your move?"), reply_markup=k.game_rps())

    await game_timer(message, state)
