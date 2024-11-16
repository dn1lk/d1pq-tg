import asyncio
import logging

from aiogram import Bot, types
from aiogram.fsm.context import FSMContext
from aiogram.utils import formatting
from aiogram.utils.i18n import gettext as _
from aiogram.utils.i18n import ngettext as ___

from handlers.commands.play.uno.misc.data import UnoData
from utils import TimerTasks

logger = logging.getLogger("bot.uno")


async def _get_results_text(
    bot: Bot,
    chat_id: int,
    data_uno: UnoData,
) -> formatting.Text:
    async def get_results():
        finished_players = sorted(
            (data_uno.players.finished | data_uno.players.playing).items(),
            key=lambda player: (player[1].points, player[1].cards_played),
            reverse=True,
        )

        for _enum, (finished_id, finished_data) in enumerate(finished_players, start=1):
            finished_user = await data_uno.players.get_user(bot, chat_id, finished_id)
            content = formatting.Text(
                _("WINNER") if _enum == 1 else _enum,
                ": ",
                formatting.TextMention(finished_user.first_name, user=finished_user),
                " — ",
                ___(
                    "1 card played",
                    "{amount} cards played",
                    finished_data.cards_played,
                ).format(amount=finished_data.cards_played),
                ", ",
                ___(
                    "1 point earned",
                    "{points} points earned",
                    finished_data.points,
                ).format(points=finished_data.points),
                ".",
            )

            yield content

    return formatting.as_list(*[result async for result in get_results()])


async def start(
    bot: Bot,
    state: FSMContext,
    timer: TimerTasks,
    data_uno: UnoData,
) -> None:
    logger.debug("[UNO] start executing: %s", data_uno)

    first_card = data_uno.deck.last_card
    message = await bot.send_sticker(state.key.chat_id, first_card.file_id)

    from .turn import proceed_state

    content = formatting.Text(_("The first card is discarded."))
    await proceed_state(message, bot, state, timer, data_uno, content)


async def restart(
    bot: Bot,
    state: FSMContext,
    timer: TimerTasks,
    data_uno: UnoData,
) -> None:
    logger.debug("[UNO] restart executing: %s", data_uno)
    from .timer import clear

    clear(state, timer)

    _results = await _get_results_text(bot, state.key.chat_id, data_uno)
    data_uno.restart()

    content = formatting.Text(formatting.Bold(_("Round over.")), "\n\n", _results)

    message = await bot.send_message(
        state.key.chat_id,
        **content.as_kwargs(),
    )

    content = formatting.Text(_("New round starts in"), " ", formatting.Bold(3), "...")

    message = await message.answer(**content.as_kwargs())
    assert isinstance(message, types.Message), "wrong message"

    await asyncio.sleep(1)

    for n in range(2, 1, -1):
        message = await message.edit_text(message.md_text.replace(str(n + 1), str(n)))
        assert isinstance(message, types.Message), "wrong message"

        await asyncio.sleep(1)

    await message.delete()
    await start(bot, state, timer, data_uno)


async def finish(
    bot: Bot,
    state: FSMContext,
    timer: TimerTasks,
    data_uno: UnoData,
) -> None:
    logger.debug("[UNO] finish executing: %s", data_uno)
    from .timer import clear

    clear(state, timer)

    _results = await _get_results_text(bot, state.key.chat_id, data_uno)
    await data_uno.clear(state)

    content = formatting.Text(formatting.Bold(_("Game over.")), "\n\n", _results)

    await bot.send_message(
        state.key.chat_id,
        **content.as_kwargs(),
    )
