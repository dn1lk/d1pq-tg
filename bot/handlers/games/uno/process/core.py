import asyncio
from random import choice, random

from aiogram import types, html
from aiogram.fsm.context import FSMContext
from aiogram.utils.i18n import gettext as _, ngettext as ___

from bot.handlers import get_username
from .cards import UnoColors, UnoEmoji
from .data import UnoData, UnoStats
from ..settings import UnoSettings, UnoDifficulty
from ... import keyboards as k


async def start(
        message: types.Message,
        state: FSMContext,
        user_ids: list[int],
        settings: UnoSettings,
        winners: dict[int, UnoStats] = None
):
    data = await UnoData.start(state, user_ids, settings, winners)
    message = await message.answer_sticker(data.current_card.file_id)
    await proceed_turn(message, state, data, _("The first card is discarded."))


async def proceed_uno(message: types.Message, state: FSMContext, data: UnoData, user: types.User):
    uno_user = message.entities[0].user if message.entities else await state.bot.get_me()

    if user.id == uno_user.id:
        return asyncio.current_task().cancel()

    data.pick_card(uno_user, 2)
    await data.update(state)

    answer = choice(
        (
            _("{user} gifts player {uno_user} 2 cards."),
            _("{user} gives player {uno_user} 2 cards."),
            _("{user} presents player {uno_user} with 2 cards."),
        )
    )

    await message.edit_text(answer.format(user=get_username(user), uno_user=get_username(uno_user)))


async def kick_for_kick(state: FSMContext, data: UnoData, user: types.User):
    await data.remove_user(state, user.id)
    await state.update_data(uno=data.dict())

    answer = _("{user} is kicked from the game for kick out of this chat.").format(user=get_username(user))
    await state.bot.send_message(state.key.chat_id, answer)

    if not data.settings.mode or len(data.users) == 1:
        await finish(state, data)


async def kick_for_idle(message: types.Message, state: FSMContext, data: UnoData, user: types.User):
    await data.remove_user(state, user.id)
    await data.update(state)

    answer = _("{user} is kicked from the game.").format(user=get_username(user))
    await message.answer(answer)

    if not data.settings.mode or len(data.users) == 1:
        await finish(state, data)


async def kick_for_cards(message: types.Message, state: FSMContext, data: UnoData):
    await data.remove_user(state, message.from_user.id)
    await data.update(state)

    if message.from_user.id == state.bot.id:
        answer = _("Well, I have run out of my hand. I have to remain only an observer =(.")
    else:
        answer = _("{user} puts his last card and leaves the game as the winner.").format(
            user=get_username(message.from_user)
        )

    await message.answer(answer)


async def pre(message: types.Message, state: FSMContext, data: UnoData, answer: str):
    for task in asyncio.all_tasks():
        if task.get_name().startswith('uno') and task is not asyncio.current_task():
            task.cancel()

    data.update_turn(message.from_user.id)
    await proceed_turn(message, state, data, answer)


async def proceed_pass(message: types.Message, state: FSMContext, data: UnoData) -> types.Message:
    for task in asyncio.all_tasks():
        if task.get_name().startswith('uno') and task is not asyncio.current_task():
            task.cancel()

    if data.current_user_id == state.bot.id:
        user = state.bot.id
        data.current_state.passed = user
    else:
        user = message.from_user
        data.current_state.passed = user.id

    answer = data.play_draw(user)
    return await post(message, state, data, answer)


async def proceed_turn(message: types.Message, state: FSMContext, data: UnoData, answer: str = ""):
    if data.current_card.color is UnoColors.black:
        if data.current_user_id == state.bot.id:
            from .bot import UnoBot
            bot = UnoBot(message, state, data)

            answer_color = bot.gen_color()
            await message.answer(answer_color)
        else:
            await data.update(state)

            answer_color = choice(
                (
                    _("Finally, we will change the color.\nWhat will {user} choose?"),
                    _("New color, new light.\nby {user}."),
                )
            )

            return await message.answer(
                answer_color.format(user=get_username(message.from_user)),
                reply_markup=k.uno_color(),
            )

    elif data.settings.seven_0 and data.current_card.emoji == UnoEmoji.seven and data.users[data.current_user_id]:
        if len(data.users) == 2:
            seven_user = await data.get_user(state, data.next_user_id)
            answer_seven = data.play_seven(message.from_user, seven_user)
            await message.answer(answer_seven)

        elif data.current_user_id == state.bot.id:
            from .bot import UnoBot
            bot = UnoBot(message, state, data)

            answer_seven = await bot.gen_seven()
            await message.answer(answer_seven)

        else:
            await data.update(state)

            answer_seven = _(
                "{user}, with whom will you exchange cards?\n"
                "Mention (@) this player in your next message."
            )

            return await message.answer(
                answer_seven.format(user=get_username(message.from_user)),
            )

    answer = data.update_state() or answer

    if answer:
        user = await data.get_user(state)
        answer = answer.format(user=get_username(user))

    return await post(message, state, data, answer)


async def post(message: types.Message, state: FSMContext, data: UnoData, answer: str):
    data.current_index = data.next_index

    from .bot import UnoBot
    bot = UnoBot(message, state, data)

    if len(data.users[message.from_user.id]) == 1:
        answer_uno = data.update_uno(message.from_user)
        bot.message = await message.answer(answer_uno, reply_markup=k.uno_say())

        asyncio.create_task(bot.gen_uno(), name=f'{bot}:uno')

    elif not data.users[message.from_user.id]:
        await kick_for_cards(message, state, data)

        if data.settings.mode or len(data.users) == 1:
            if data.current_state.drawn:
                user = state.bot.id if data.current_user_id == state.bot.id else await data.get_user(state)
                data.play_draw(user)

            return await finish(state, data)

    await data.update(state)

    if data.current_user_id != state.bot.id:
        answer_next = choice(
            (
                _("{user}, your turn."),
                _("{user}, your move."),
                _("Now {user} is moving."),
                _("Player's turn {user}."),
                _("I pass the turn to the player {user}."),
            )
        ).format(user=get_username(await data.get_user(state)))

        message = await message.reply(
            f'{answer}\n{answer_next}',
            reply_markup=k.uno_show_cards(data.current_state.bluffed),
        )

        from . import timeout, timeout_exception
        from ... import timer

        timer(state, timeout, timeout_exception, message=message)

    elif data.current_state.bluffed:
        m = data.settings.difficulty

        if data.settings.difficulty is UnoDifficulty.normal:
            m /= len(data.users[data.prev_user_id])
        elif data.settings.difficulty is UnoDifficulty.hard:
            m /= len([card for card in data.users[data.prev_user_id] if card.color is data.deck[-1].color]) or 0.5

        if random() < 1 / m:
            answer = await data.play_bluff(state)
            return post(message, state, data, answer)

    cards = tuple(bot.get_cards())

    if cards or data.current_user_id == state.bot.id:
        asyncio.create_task(bot.gen_turn(cards), name=str(bot))


async def finish(state: FSMContext, data: UnoData) -> types.Message:
    async def get_answer_winners():
        for enum, winner in enumerate(sorted(data.stats.items(), key=lambda i: i[1].points, reverse=True), start=1):
            winner_id, winner_data = winner

            if not data.settings.mode or winner_data.points:
                user = await data.get_user(state, winner_id)

                if enum == 1:
                    enum = _("WINNER")

                answer_cards = ___(
                    "card played",
                    "{amount} cards played",
                    winner_data.cards_played,
                ).format(amount=winner_data.cards_played)

                answer_points = ___(
                    "point earned",
                    "{points} points earned",
                    winner_data.points,
                ).format(points=winner_data.points)

                yield f'{enum}: {get_username(user)} - {answer_cards}, {answer_points}.'

    await data.finish(state)
    answer = '\n\n' + '\n'.join([winner async for winner in get_answer_winners()])

    if not data.settings.mode or max(winner_data.points for winner_data in data.stats.values()) >= 500:
        message = await state.bot.send_message(state.key.chat_id, html.bold(_("Game over.")) + answer)
    else:
        message = await state.bot.send_message(state.key.chat_id, html.bold(_("Round over.")) + answer)
        await start(message, state, list(data.stats), data.settings, data.stats)

    return message
