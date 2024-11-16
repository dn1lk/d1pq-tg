import logging

from aiogram import Bot, types
from aiogram.fsm.context import FSMContext
from aiogram.utils import formatting
from aiogram.utils.i18n import gettext as _

from handlers.commands.play.uno.misc import keyboards
from handlers.commands.play.uno.misc.data import UnoData
from utils import TimerTasks

logger = logging.getLogger("bot.uno")


async def kick_for_cards(bot: Bot, state: FSMContext, data_uno: UnoData, user: types.User) -> None:
    logger.debug("[UNO] kick for cards executing: %s", data_uno)

    data_uno.players.finish_player(user.id)
    await data_uno.set_data(state)

    player_data = data_uno.players.finished[user.id]

    if player_data.is_me:
        content = formatting.Text(_("Well, I have run out of my hand. I have to remain only an observer. 🫣"))
    else:
        content = formatting.Text(
            formatting.TextMention(user.first_name, user=user),
            " ",
            _(
                "puts last card and leaves the game as the winner",
            ),
            ".",
        )

    await bot.send_message(state.key.chat_id, **content.as_kwargs())


async def _kick(
    bot: Bot,
    state: FSMContext,
    timer: TimerTasks,
    data_uno: UnoData,
    content: formatting.Text,
    *,
    is_current: bool,
) -> None:
    if is_current:
        content = formatting.Text(content, "\n", await data_uno.do_next(bot, state))
        message = await bot.send_message(
            state.key.chat_id,
            reply_markup=keyboards.show_cards(bluffed=data_uno.state.bluffed),
            **content.as_kwargs(),
        )

        from .turn import update_timer

        await update_timer(message, bot, state, timer, data_uno)
    else:
        await data_uno.set_data(state)
        await bot.send_message(state.key.chat_id, **content.as_kwargs())


async def kick_for_kick(
    bot: Bot,
    state: FSMContext,
    timer: TimerTasks,
    data_uno: UnoData,
    user: types.User,
) -> None:
    """Kick player from the game for kick from the chat"""

    logger.debug("[UNO] kick for kick executing: %s", data_uno)

    current_id = data_uno.players.current_id
    await data_uno.players.kick_player(state, data_uno.deck, user.id)

    content = formatting.Text(
        formatting.TextMention(user.first_name, user=user),
        " ",
        _("is also kicked from the game"),
        ".",
    )

    await _kick(bot, state, timer, data_uno, content, is_current=user.id == current_id)


async def kick_for_idle(
    bot: Bot,
    state: FSMContext,
    timer: TimerTasks,
    data_uno: UnoData,
    user: types.User,
) -> None:
    """Kick player from the game for idling"""

    logger.debug("[UNO] kick for idle executing: %s", data_uno)

    current_id = data_uno.players.current_id
    await data_uno.players.kick_player(state, data_uno.deck, user.id)

    content = formatting.Text(
        formatting.TextMention(user.first_name, user=user),
        " ",
        _("is kicked from the game"),
        ".",
    )

    await _kick(bot, state, timer, data_uno, content, is_current=user.id == current_id)
