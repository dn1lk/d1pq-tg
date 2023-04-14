import asyncio

from aiogram import html
from aiogram.fsm.context import FSMContext
from aiogram.utils.i18n import gettext as _, ngettext as ___

from bot.core.utils import TimerTasks
from ..data import UnoData
from ..data.settings import UnoSettings
from ..data.settings.modes import UnoMode


async def start(
        state: FSMContext,
        timer: TimerTasks,
        user_ids: list[int],
        settings: UnoSettings,
):
    data_uno = await UnoData.setup(state, user_ids, settings)
    await restart(state, timer, data_uno)


async def restart(
        state: FSMContext,
        timer: TimerTasks,
        data_uno: UnoData,
):
    await data_uno.set_data(state)

    first_card = data_uno.deck.last_card
    message = await state.bot.send_sticker(state.key.chat_id, first_card.file_id)

    from .turn import proceed_action
    await proceed_action(message, state, timer, data_uno, _("The first card is discarded."))


async def finish(
        state: FSMContext,
        timer: TimerTasks,
        data_uno: UnoData
):
    del timer[state.key]

    timer_poll = TimerTasks('uno_poll')
    del timer_poll[state.key]

    if (
            data_uno.settings.mode is UnoMode.FAST
            or max(player.points for player in data_uno.players) >= 500
    ):
        await data_uno.clear(state)

        answer = await _get_results_answer(state, data_uno)
        await state.bot.send_message(
            state.key.chat_id,
            f'{html.bold(_("Game over."))}\n\n{answer}'
        )
    else:
        data_uno.restart()

        answer = await _get_results_answer(state, data_uno)
        message = await state.bot.send_message(
            state.key.chat_id,
            f'{html.bold(_("Round over."))}\n\n{answer}'
        )

        message = await message.answer(_("New round starts in {delay}...").format(delay=html.bold(10)))

        for n in range(9, 0, -1):
            await asyncio.sleep(1)
            message = await message.edit_text(message.html_text.replace(str(n + 1), str(n)))

        await message.delete()
        await restart(state, timer, data_uno)


async def _get_results_answer(
        state: FSMContext,
        data_uno: UnoData
) -> str:
    async def get_results():
        finished_players = sorted(data_uno.players.finished, key=lambda p: p.points, reverse=True)

        for enum, finished_player in enumerate(finished_players, start=1):
            if (
                    data_uno.settings.mode is UnoMode.FAST
                    or finished_player.points
            ):
                if enum == 1:
                    enum = _("WINNER")

                answer_one = ___(
                    "1 card played",
                    "{amount} cards played",
                    finished_player.cards_played,
                ).format(amount=finished_player.cards_played)

                answer_two = ___(
                    "1 point earned",
                    "{points} points earned",
                    finished_player.points,
                ).format(points=finished_player.points)

                finished_user = await finished_player.get_user(state.bot, state.key.chat_id)
                yield f'{enum}: {finished_user.mention_html()} - {answer_one}, {answer_two}.'

    return '\n'.join([result async for result in get_results()])
