import asyncio
from random import choice

from aiogram import types
from aiogram.fsm.context import FSMContext
from aiogram.utils.i18n import gettext as _, ngettext as ___

from bot.handlers import get_username
from .cards import UnoColors, UnoEmoji
from .data import UnoData
from .exceptions import UnoNoCardsException, UnoOneCardException
from .. import keyboards as k


async def uno(message: types.Message, data: UnoData, state: FSMContext):
    from .bot import UnoBot

    bot = UnoBot(message, state.bot, data)

    if message.from_user.id == state.bot.id:
        coro = bot.uno
        answer = _("I have one card left!")
    else:
        coro = bot.uno_user
        answer = _("Player {user} has one card left!").format(user=get_username(message.from_user))

    bot.message = await message.answer(answer, reply_markup=k.uno_uno())
    asyncio.create_task(coro(state), name=str(bot) + ':' + str(message.from_user.id) + ':' + 'uno')


async def skip(message: types.Message, data: UnoData, state: FSMContext):
    special = await data.apply_current_special(state)

    if special:
        await message.answer(special)

    data.current_skip = data.current_user_id

    user = await state.bot.get_me() if data.current_user_id == state.bot.id else message.from_user
    await post(message, data, state, await data.add_card(state.bot, user))


async def color(message: types.Message, data: UnoData, state: FSMContext, accept: str):
    if message.from_user.id == state.bot.id:
        from .bot import UnoBot

        bot = UnoBot(message, state.bot, data)

        await message.answer(bot.get_color())
        await process(message, data, state, accept)
    else:
        message = await message.reply(
            data.special_color().format(user=get_username(message.from_user)),
            reply_markup=k.uno_color()
        )

        await state.update_data(uno=data.dict())

        from . import uno_timeout
        from .. import timer

        timer(state, uno_timeout, message=message)


async def remove(message: types.Message, data: UnoData, state: FSMContext):
    if message.from_user.id == state.bot.id:
        answer = _("Well, I have run out of cards. I have to remain only an observer =(.")
    else:
        answer = _("{user} puts his last card and leaves the game as the winner.").format(
            user=get_username(message.from_user)
        )

    await message.answer(answer)
    await data.remove_user(state)


async def finish(message: types.Message, data: UnoData, state: FSMContext):
    answer = await data.finish(state)

    for number, winner in enumerate(data.winners.items(), start=1):
        user = (await state.bot.get_chat_member(message.chat.id, winner[0])).user
        answer += "\n{number}: {user} - ".format(
            number=_("WINNER") if number == 1 else number,
            user=get_username(user)
        ) + ___("{amount} card played.", "{amount} cards played.", winner[1]).format(
            amount=winner[1]
        )

    await message.answer(answer)


async def post(message: types.Message, data: UnoData, state: FSMContext, answer: str):
    data.current_user_id = data.next_user_id
    await state.update_data(uno=data.dict())

    from .bot import UnoBot

    bot = UnoBot(message, state.bot, data)
    cards = bot.get_cards()

    if cards or data.current_user_id == state.bot.id:
        asyncio.create_task(bot.gen(state, cards), name=str(bot))
    else:
        user = (await state.bot.get_chat_member(message.chat.id, data.current_user_id)).user
        message = await message.reply(
            answer + "\n\n" + choice(
                (
                    _("{user}, your turn."),
                    _("{user}, your move."),
                    _("Now {user} is moving."),
                    _("Player's turn {user}."),
                    _("I pass the turn to the player {user}."),
                )
            ).format(user=get_username(user)),
            reply_markup=k.uno_show_cards(),
        )

        from . import uno_timeout
        from .. import timer

        timer(state, uno_timeout, message=message)


async def process(message: types.Message, data: UnoData, state: FSMContext, accept: str = ""):
    if data.current_card.color is UnoColors.black:
        return await color(message, data, state, accept)

    if data.current_card.emoji != UnoEmoji.draw:
        special = await data.apply_current_special(state)

        if special:
            await message.answer(special)

    special = await data.update_current_special()

    if special:
        user = (await state.bot.get_chat_member(message.chat.id, data.current_user_id)).user
        accept = special.format(user=get_username(user))

    await post(message, data, state, accept)


async def pre(message: types.Message, data: UnoData, state: FSMContext, accept: str):
    try:
        data.update_current_user_id(message.from_user.id)
    except UnoOneCardException:
        await uno(message, data, state)
    except UnoNoCardsException:
        await remove(message, data, state)

    await process(message, data, state, accept.format(user=get_username(message.from_user)))
