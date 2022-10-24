import asyncio
from random import choice, random

from aiogram import types
from aiogram.fsm.context import FSMContext
from aiogram.utils.i18n import gettext as _, ngettext as ___

from bot.handlers import get_username
from .cards import UnoColors, UnoEmoji
from .data import UnoData
from .exceptions import UnoNoCardsException, UnoOneCardException
from ... import keyboards as k


async def say_uno(message: types.Message, data: UnoData, state: FSMContext):
    from .bot import UnoBot

    bot = UnoBot(message, state.bot, data)

    if message.from_user.id == state.bot.id:
        answer = _("I have one card left!")
        coro = bot.uno
    else:
        answer = _("Player {user} has one card left!").format(user=get_username(message.from_user))
        coro = bot.uno_user

    bot.message = await message.answer(answer, reply_markup=k.uno_uno())
    asyncio.create_task(coro(state), name=f'{bot}:{message.from_user.id}:uno')


async def pass_turn(message: types.Message, data: UnoData, state: FSMContext):
    special = await data.apply_current_special(state)

    if special:
        await message.answer(special)

    data.current_special.passed = data.current_user_id

    user = await state.bot.get_me() if data.current_user_id == state.bot.id else message.from_user
    await post(message, data, state, data.add_card(state.bot, user))


async def change_color(message: types.Message, data: UnoData, state: FSMContext, accept: str):
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
        from ... import timer

        timer(state, uno_timeout, message=message)


async def kick_for_cards(message: types.Message, data: UnoData, state: FSMContext):
    if message.from_user.id == state.bot.id:
        answer = _("Well, I have run out of my hand. I have to remain only an observer =(.")
    else:
        answer = _("{user} puts his last card and leaves the game as the winner.").format(
            user=get_username(message.from_user)
        )

    await message.answer(answer)
    await data.remove_user(state)


async def kick_for_inactivity(message: types.Message, data: UnoData, state: FSMContext, user: types.User):
    await data.remove_user(state, user.id)
    await message.answer(_("{user} is kicked from the game.").format(user=get_username(user)))


async def finish(message: types.Message, data: UnoData, state: FSMContext):
    answer = await data.finish(state)

    for number, winner in enumerate(dict(sorted(data.winners.items(), key=lambda i: i[1].points)).items(), start=1):
        winner_id, winner_data = winner
        user = await data.get_user(state, winner_id)
        answer += f'\n\n{_("WINNER") if number == 1 else number}: {get_username(user)} - ' + \
                  ___(
                      "{amount} card played,",
                      "{amount} cards played,",
                      winner_data.cards_played,
                  ).format(amount=winner_data.cards_played) + \
                  " " + \
                  ___(
                      "{points} point earned.",
                      "{points} points earned.",
                      winner_data.points,
                  ).format(points=winner_data.points)

    message = await message.answer(answer)

    if data.users:
        await post(message, data, state, _("Next round!"))


async def post(message: types.Message, data: UnoData, state: FSMContext, answer: str):
    data.current_index = data.next_index

    if data.prev_user_id == state.bot.id and data.current_card and \
            data.current_card.cost == 50 and data.current_special.drawn and \
            random() < 1 / data.settings.difficulty:
        await message.reply(await data.check_draw_black_card(state))

    await state.update_data(uno=data.dict())

    from .bot import UnoBot

    bot = UnoBot(message, state.bot, data)
    cards = bot.get_cards()

    if cards or data.current_user_id == state.bot.id:
        asyncio.create_task(bot.gen(state, cards), name=str(bot))
    else:
        message = await message.reply(
            answer + "\n\n" + choice(
                (
                    _("{user}, your turn."),
                    _("{user}, your move."),
                    _("Now {user} is moving."),
                    _("Player's turn {user}."),
                    _("I pass the turn to the player {user}."),
                )
            ).format(user=get_username(await data.get_user(state))),
            reply_markup=k.uno_show_cards(data.current_card),
        )

        from . import uno_timeout
        from ... import timer

        timer(state, uno_timeout, message=message)


async def process(message: types.Message, data: UnoData, state: FSMContext, accept: str = ""):
    if data.current_card.color is UnoColors.black:
        return await change_color(message, data, state, accept)

    if data.current_card.emoji != UnoEmoji.draw:
        special = await data.apply_current_special(state)

        if special:
            await message.answer(special)

    special = data.update_current_special()

    if special:
        accept = special.format(user=get_username(await data.get_user(state)))

    await post(message, data, state, accept)


async def pre(message: types.Message, data: UnoData, state: FSMContext, accept: str):
    try:
        data.update_turn(message.from_user.id)
    except UnoOneCardException:
        await say_uno(message, data, state)
    except UnoNoCardsException:
        await kick_for_cards(message, data, state)

    await process(message, data, state, accept.format(user=get_username(message.from_user)))
