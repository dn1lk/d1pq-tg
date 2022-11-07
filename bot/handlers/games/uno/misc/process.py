import asyncio
from random import choice

from aiogram import types, html
from aiogram.fsm.context import FSMContext
from aiogram.utils.i18n import gettext as _, ngettext as ___

from bot.handlers import get_username
from bot.utils.timer import Timer
from .data import UnoData, UnoStats
from ..settings import UnoSettings
from . import keyboards as k


async def start(
        message: types.Message,
        state: FSMContext,
        timer: Timer,
        user_ids: list[int],
        settings: UnoSettings,
        stats: dict[int, UnoStats] = None
):
    data = await UnoData.start(state, user_ids, settings, stats or {})
    message = await message.answer_sticker(data.current_card.file_id)

    from .bot import UnoBot
    bot = UnoBot(message, state, data)

    await bot.proceed_turn(timer, _("The first card is discarded."))


async def proceed_uno(message: types.Message, state: FSMContext, data: UnoData, user: types.User):
    uno_user = message.entities[0].user

    if user.id == uno_user.id:
        return

    data.pick_card(uno_user, 2)
    await data.set_data(state)

    answer = choice(
        (
            _("{user} gifts player {uno_user} 2 cards."),
            _("{user} gives player {uno_user} 2 cards."),
            _("{user} presents player {uno_user} with 2 cards."),
        )
    )

    await message.edit_text(answer.format(user=get_username(user), uno_user=get_username(uno_user)))


async def kick_for_kick(state: FSMContext, timer: Timer, data: UnoData, user: types.User):
    await data.remove_user(state, user.id)
    await data.set_data(state)

    answer = _("{user} is kicked from the game for kick out of this chat.").format(user=get_username(user))
    await state.bot.send_message(state.key.chat_id, answer)

    if not data.settings.mode or len(data.users) == 1:
        await finish(state, timer, data)


async def kick_for_idle(message: types.Message, state: FSMContext, timer: Timer, data: UnoData, user: types.User):
    await data.remove_user(state, user.id)
    await data.set_data(state)

    answer = _("{user} is kicked from the game.").format(user=get_username(user))
    await message.answer(answer)

    if not data.settings.mode or len(data.users) == 1:
        await finish(state, timer, data)


async def kick_for_cards(message: types.Message, state: FSMContext, data: UnoData):
    await data.remove_user(state, message.from_user.id)
    await data.set_data(state)

    if message.from_user.id == state.bot.id:
        answer = _("Well, I have run out of my hand. I have to remain only an observer =(.")
    else:
        answer = _("{user} puts his last card and leaves the game as the winner.").format(
            user=get_username(message.from_user)
        )

    await message.answer(answer)


async def proceed_turn(
        message: types.Message,
        state: FSMContext,
        timer: Timer,
        data_uno: UnoData,
        answer: str = ""
) -> types.Message:
    user = await data_uno.get_user(state)
    answer = answer.format(user=get_username(user))

    return await next_turn(message, state, timer, data_uno, answer)


async def next_turn(
        message: types.Message,
        state: FSMContext,
        timer: Timer,
        data: UnoData,
        answer: str
) -> types.Message:
    data.current_index = data.next_index

    from .bot import UnoBot
    bot = UnoBot(message, state, data)

    if len(data.users[message.from_user.id]) == 1:
        answer_uno = data.update_uno(message.from_user)
        bot.message = await message.answer(answer_uno, reply_markup=k.say_uno())

        timer[timer.get_name(state, 'game:uno')] = asyncio.create_task(bot.gen_uno())

    elif not data.users[message.from_user.id]:
        await kick_for_cards(message, state, data)

        if data.settings.mode or len(data.users) == 1:
            if data.current_state.drawn:
                user = state.bot.id if data.current_user_id == state.bot.id else await data.get_user(state)
                data.play_draw(user)

            return await finish(state, timer, data)

    await data.set_data(state)

    cards = tuple(bot.get_cards())

    if not cards or data.current_user_id == state.bot.id:
        if data.current_user_id == state.bot.id:
            answer_next = _("My turn.")
        else:
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
            reply_markup=k.show_cards(data.current_state.bluffed),
        )

    if cards or data.current_user_id == state.bot.id:
        timer_name = timer.get_name(state, 'game')
        await timer.cancel(timer_name)

        timer[timer_name] = asyncio.create_task(bot.gen_turn(timer, cards))
    else:
        from . import timeout, timeout_done
        await timer.create(state, timeout, timeout_done, name='game', message=message, timer=timer)


async def finish(state: FSMContext, timer: Timer, data: UnoData) -> types.Message:
    await timer.cancel(timer.get_name(state, 'game'))
    await data.finish(state)

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

    answer = '\n\n' + '\n'.join([winner async for winner in get_answer_winners()])

    if not data.settings.mode or max(winner_data.points for winner_data in data.stats.values()) >= 500:
        message = await state.bot.send_message(state.key.chat_id, html.bold(_("Game over.")) + answer)
    else:
        message = await state.bot.send_message(state.key.chat_id, html.bold(_("Round over.")) + answer)
        await start(message, state, timer, list(data.stats), data.settings, data.stats)

    return message
