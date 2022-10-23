import asyncio
from random import choice

from aiogram import Router, Bot, F, types, flags
from aiogram.fsm.context import FSMContext
from aiogram.utils.chat_action import ChatActionSender
from aiogram.utils.i18n import I18n, gettext as _

from . import Game, keyboards as k, timer, win_timeout
from .. import get_username
from ..settings.commands.filter import CustomCommandFilter

router = Router(name='game:core')
router.message.filter(CustomCommandFilter(commands=['play', 'поиграем']))


@router.message(F.text.endswith(('uno', 'уно')))
async def uno_handler(message: types.Message, bot: Bot, state: FSMContext):
    from .uno.settings import UnoDifficulty, UnoMode
    message = await message.answer(
        _(
            "<b>Let's play UNO?</b>\n\n"
            "One minute to make a decision!\n"
            "Difficulty: <b>{difficulty}</b>.\n"
            "Mode: <b>{mode}</b>\n\n"
            "<b>Already in the game:</b>\n"
            "{user}"
        ).format(
            user=get_username(message.from_user),
            difficulty=UnoDifficulty.normal.word,
            mode=UnoMode.fast.word,
        ),
        reply_markup=k.uno_start(),
    )

    from .uno.core import start_timer

    timer(state, start_timer, message=message, bot=bot)


@router.message(F.text.endswith(('cts', 'грд')))
async def cts_handler(message: types.Message, state: FSMContext, i18n: I18n):
    message = await message.answer(
        _(
            "Oh, the game of cities. Well, let's try!\n\n"
            "The rules are as follows: you need to answer the name of the settlement, "
            "starting with the last letter of the name of the previous settlement.\n"
            "You have 60 seconds to think."
        )
    )

    if choice(('bot', 'user')) == 'bot':
        from .cts import get_cities

        bot_var = choice(get_cities(i18n.current_locale))
        cities = [bot_var]
        answer = _("I start! My word: {bot_var}.").format(bot_var=bot_var)
    else:
        bot_var = None
        cities = []
        answer = _("You start! Your word?")

    from bot.handlers.games.cts.data import CtsData

    await state.set_state(Game.cts)
    await state.update_data(cts=CtsData(bot_var=bot_var, cities=cities).dict())
    timer(state, win_timeout, message=await message.answer(answer))


@router.message(F.chat.type == 'private', F.text.endswith(('rnd', 'рнд')))
async def rnd_private_handler(message: types.Message, state: FSMContext):
    await message.answer(
        _(
            "Hmm, you are trying your luck... Well, ender any number between 1 and 10 and I'll choose "
            "my own and we find out if our thoughts are the same ;)."
        )
    )
    await state.set_state(Game.rnd)


@router.message(F.text.endswith(('rnd', 'рнд')))
@flags.data('stickers')
async def rnd_chat_handler(message: types.Message, bot: Bot, state: FSMContext, stickers: list):
    message = await message.answer(
        _(
            "Mm, {user} is trying his luck... Well, EVERYONE, EVERYONE, EVERYONE, pay attention!\n\n"
            "Enter any number between 1 and 10 and I'll choose "
            "my own in 60 seconds and we'll see which one of you is right."
        ).format(user=get_username(message.from_user))
    )

    async with ChatActionSender.typing(chat_id=message.chat.id):
        await asyncio.sleep(2)

        await state.set_state(Game.rnd)
        message = await message.answer(_("LET THE BATTLE BEGIN!"))

    asyncio.create_task(rnd_finish_handler(message, bot, state, stickers))


async def rnd_finish_handler(message: types.Message, bot: Bot, state: FSMContext, stickers: list | None):
    async with ChatActionSender.choose_sticker(chat_id=message.chat.id, interval=20):
        await asyncio.sleep(60)

        if await state.get_state() == Game.rnd.state:
            await state.set_state()

        stickers = sum([(await bot.get_sticker_set(sticker_set)).stickers for sticker_set in stickers], [])
        message = await message.reply_sticker(
            choice([sticker.file_id for sticker in stickers if sticker.emoji in ('⏳', '🙈')])
        )

    bot_var = str(choice(range(1, 11)))

    data = await state.get_data()
    winners = [
        get_username((await bot.get_chat_member(message.chat.id, user_id)).user) for user_id in
        data.pop('rnd', {}).get(bot_var, ())
    ]
    await state.set_data(data)

    answer = _("So, my variant is {bot_var}.\n").format(bot_var=bot_var)

    if winners:
        answer += _('This time the title of winner goes to: {winners}. Congratulations!').format(
            winners=', '.join(winners)
        )
    else:
        answer = _("Well... no one guessed right. Heh.")

    await message.answer(answer)


@router.message(F.text.endswith(('rps', 'кнб')))
async def rps_handler(message: types.Message):
    await message.answer(
        _("Eh, classic. {user}, your turn.").format(user=get_username(message.from_user)),
        reply_markup=k.rps_show_vars()
    )
