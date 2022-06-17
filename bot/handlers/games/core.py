import asyncio
from random import choice

from aiogram import Router, Bot, F, types, flags
from aiogram.dispatcher.fsm.context import FSMContext
from aiogram.utils.chat_action import ChatActionSender
from aiogram.utils.i18n import I18n, gettext as _

from bot import keyboards as k

from . import Game, timer, get_cts, win_timeout, close_timeout
from .. import get_username
from ..settings.commands.filter import CustomCommandFilter
from ..settings.commands.middleware import CustomCommandsMiddleware

router = Router(name='game:core')
router.message.filters[1] = CustomCommandFilter
router.edited_message.filters[1] = CustomCommandFilter

router.message.outer_middleware(CustomCommandsMiddleware())
router.edited_message.outer_middleware(CustomCommandsMiddleware())

router.message.filter(commands=['play', 'поиграем'], commands_ignore_case=True)


@router.message(F.text.lower().endswith(('uno', 'уно')))
async def uno_handler(message: types.Message, bot: Bot, state: FSMContext):
    message = await message.answer(
        _(
            "<b>Let's play UNO?</b>\n\n"
            "One minute to make a decision!\n"
            "Game initiator - {user}.\n\n"
            "<b>Already in the game:</b>\n"
            "{user}"
        ).format(user=get_username(message.from_user)),
        reply_markup=k.game_uno_start(),
    )

    from .uno.core import start_handler

    timer(state, start_handler, query=message, bot=bot)


@router.message(F.text.lower().endswith(('cts', 'грд')))
async def cts_handler(message: types.Message, state: FSMContext, i18n: I18n):
    message = await message.answer(
        _(
            "Oh, the game of cities. Well, let's try!\n\n"
            "The rules are as follows: you need to answer the name of the settlement, "
            "starting with the last letter of the name of the previous settlement.\n"
            "You have 60 seconds to think."
        )
    )

    if choice(('bot_var', 'user_var')) == 'bot_var':
        bot_var = choice(get_cts(i18n.current_locale))
        answer = _("I start! My word: {bot_var}.").format(bot_var=bot_var)
    else:
        bot_var = None
        answer = _("You start! Your word?")

    await state.set_state(Game.cts)
    await state.update_data(cts=(bot_var, [bot_var], 5))
    timer(state, win_timeout, message=await message.answer(answer))


@router.message(F.text.lower().endswith(('rnd', 'рнд')))
@flags.data('stickers')
async def rnd_handler(message: types.Message, bot: Bot, state: FSMContext, stickers: list):
    message = await message.answer(
        _(
            "Mm, {user} is trying his luck... Well, EVERYONE, EVERYONE, EVERYONE, pay attention!\n\n"
            "Enter any emoji between 1 and 10 and I'll choose "
            "my own in 60 seconds and we'll we'll see which one of you is right."
        ).format(
            username=get_username(message.from_user)
            )
        )

    async with ChatActionSender.typing(chat_id=message.chat.id):
        await asyncio.sleep(2)

        await state.set_state(Game.rnd)
        await message.answer(_("LET THE BATTLE BEGIN!"))

    asyncio.create_task(rnd_finish_handler(message, bot, state, stickers))


async def rnd_finish_handler(message: types.Message, bot: Bot, state: FSMContext, stickers: list):
    async with ChatActionSender.choose_sticker(chat_id=message.chat.id, interval=20):
        await asyncio.sleep(60)

        stickers = sum(
            [(await bot.get_sticker_set(sticker_set)).stickers for sticker_set in stickers + ['TextAnimated']],
            []
        )
        await bot.send_sticker(
            message.chat.id,
            choice([sticker.file_id for sticker in stickers if sticker.emoji in ('⏳', '🙈')])
        )

    bot_var = str(choice(range(1, 11)))

    await state.set_state()
    message = await message.reply(_("So my variant is {bot_var}. Who guessed? Hmm...").format(bot_var=bot_var))

    data = await state.get_data()
    user_vars = data.pop('rnd', None)
    winners = [get_username(user) for user in user_vars.get(bot_var, ())] if user_vars else None

    await state.set_data(data)

    if winners:
        answer = _(
            "Well... the title of winner goes to: {winners}. Congratulations!"
        ).format(winners=", ".join(winners))
    else:
        answer = _("Well... no one guessed right. Heh.")

    await message.answer(answer)


@router.message(F.text.lower().endswith(('rps', 'кнб')))
async def rps_handler(message: types.Message, state: FSMContext):
    await state.set_state(Game.rps)
    await state.update_data(rps=(0, 0))

    await message.answer(_("Eh, classic. Your move?"), reply_markup=k.game_rps())
    timer(state, close_timeout, message=message)
