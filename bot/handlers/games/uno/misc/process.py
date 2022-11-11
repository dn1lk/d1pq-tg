import asyncio
from random import choice

from aiogram import types, html
from aiogram.fsm.context import FSMContext
from aiogram.utils.i18n import gettext as _, ngettext as ___

from bot.handlers import get_username
from bot.utils.timer import timer
from . import keyboards as k, UnoEmoji
from .data import UnoData, UnoStats, UnoSettings


async def start(
        state: FSMContext,
        user_ids: list[int],
        settings: UnoSettings,
        stats: dict[int, UnoStats] = None
):
    data = await UnoData.start(state, user_ids, settings, stats or {})
    data.update_state()

    message = await state.bot.send_sticker(state.key.chat_id, data.current_card.file_id)
    await proceed_turn(message, state, data, _("The first card is discarded."))


async def kick_for_kick(state: FSMContext, data: UnoData, user: types.User):
    await data.remove_user(state, user.id)
    await data.set_data(state)

    answer = _("{user} is kicked from the game for kick out of this chat.").format(user=get_username(user))
    await state.bot.send_message(state.key.chat_id, answer)

    if not data.settings.mode or len(data.users) == 1:
        await finish(state, data)


async def kick_for_idle(message: types.Message, state: FSMContext, data: UnoData, user: types.User):
    await data.remove_user(state, user.id)
    await data.set_data(state)

    answer = _("{user} is kicked from the game.").format(user=get_username(user))
    await message.answer(answer)

    if not data.settings.mode or len(data.users) == 1:
        await finish(state, data)


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


async def proceed_turn(
        message: types.Message,
        state: FSMContext,
        data: UnoData,
        answer: str = ""
):
    if len(data.users[message.from_user.id]) == 1:
        answer_uno = data.update_uno(message.from_user)

        from .bot import UnoBot
        timer.create(
            'game:uno',
            delay=0,
            coro=UnoBot.gen_uno(
                message=await message.answer(answer_uno, reply_markup=k.say_uno()),
                state=state,
                data=data,
            )
        )

    elif not data.users[message.from_user.id]:
        await kick_for_cards(message, state, data)

        if data.settings.mode or len(data.users) == 1:
            if data.current_state.drawn:
                data.play_draw(data.next_user_id)

            return await finish(state, data)

    user = await data.get_user(state)
    await next_turn(message, state, data, answer.format(user=get_username(user)))


async def next_turn(
        message: types.Message,
        state: FSMContext,
        data: UnoData,
        answer: str
):
    data.current_index = data.next_index
    await data.set_data(state)

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
        reply_markup=k.show_cards(data.current_card.emoji == UnoEmoji.DRAW_FOUR and data.current_state.drawn),
    )

    update_timer(message, state, data)


def update_timer(
        message: types.Message,
        state: FSMContext,
        data: UnoData,
):
    task_name = timer.get_name(state, 'game')
    from . import timeout_proceed, timeout_finally

    from .bot import UnoBot
    bot = UnoBot(message, state, data)
    cards = tuple(bot.get_cards())

    if cards or data.current_user_id == state.bot.id:
        delay = 0
        task = bot.gen_turn(cards)
    else:
        delay = 60 * data.timer_amount
        task = timeout_proceed(message, state)

    timer.create(task_name, delay, task, timeout_finally(message, state))


async def finish(state: FSMContext, data: UnoData) -> types.Message:
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
        message = await message.answer(_("New round starts in {delay}...").format(delay=html.bold(10)))

        for n in reversed(range(10)):
            await asyncio.sleep(1)
            message = await message.edit_text(message.html_text.replace(str(n + 1), str(n)))

        await message.delete()
        await start(state, list(data.stats), data.settings, data.stats)

    return message
