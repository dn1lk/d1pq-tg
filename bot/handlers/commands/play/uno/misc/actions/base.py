import asyncio

from aiogram import Bot, html
from aiogram.fsm.context import FSMContext
from aiogram.utils.i18n import gettext as _, ngettext as ___

from core.utils import TimerTasks
from ..data import UnoData


async def start(
        bot: Bot,
        state: FSMContext,
        timer: TimerTasks,
        data_uno: UnoData,
):
    first_card = data_uno.deck.last_card
    message = await bot.send_sticker(state.key.chat_id, first_card.file_id)

    from .turn import proceed_state
    await proceed_state(message, bot, state, timer, data_uno, _("The first card is discarded."))


async def restart(
        bot: Bot,
        state: FSMContext,
        timer: TimerTasks,
        data_uno: UnoData,
):
    from .timer import clear
    clear(state, timer)

    answer = await _get_results_answer(bot, state.key.chat_id, data_uno)
    data_uno.restart()

    message = await bot.send_message(
        state.key.chat_id,
        f'{html.bold(_("Round over."))}\n\n{answer}'
    )

    message = await message.answer(_("New round starts in {delay}...").format(delay=html.bold(3)))

    await asyncio.sleep(1)

    for n in range(2, 1, -1):
        message = await message.edit_text(message.html_text.replace(str(n + 1), str(n)))
        await asyncio.sleep(1)

    await message.delete()
    await start(bot, state, timer, data_uno)


async def finish(
        bot: Bot,
        state: FSMContext,
        timer: TimerTasks,
        data_uno: UnoData
):
    from .timer import clear
    clear(state, timer)

    answer = await _get_results_answer(bot, state.key.chat_id, data_uno)
    await data_uno.clear(state)

    await bot.send_message(
        state.key.chat_id,
        f'{html.bold(_("Game over."))}\n\n{answer}'
    )


async def _get_results_answer(
        bot: Bot,
        chat_id: int,
        data_uno: UnoData
) -> str:
    async def get_results():
        finished_players = sorted((data_uno.players.finished | data_uno.players.playing).items(),
                                  key=lambda player: (player[1].points, player[1].cards_played),
                                  reverse=True)

        for enum, (finished_id, finished_data) in enumerate(finished_players, start=1):
            if enum == 1:
                enum = _("WINNER")

            answer_one = ___(
                "1 card played",
                "{amount} cards played",
                finished_data.cards_played,
            ).format(amount=finished_data.cards_played)

            answer_two = ___(
                "1 point earned",
                "{points} points earned",
                finished_data.points,
            ).format(points=finished_data.points)

            finished_user = await data_uno.players.get_user(bot, chat_id, finished_id)
            yield f'{enum}: {finished_user.mention_html()} — {answer_one}, {answer_two}.'

    return '\n'.join([result async for result in get_results()])
