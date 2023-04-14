from aiogram import types
from aiogram.fsm.context import FSMContext
from aiogram.utils.i18n import gettext as _

from bot.core.utils import TimerTasks
from .base import finish
from ..data import UnoData
from ..data.settings.modes import UnoMode


async def kick_for_cards(
        state: FSMContext,
        data_uno: UnoData,
        user: types.User
):
    player = data_uno.players(user.id)

    data_uno.players.finish_player(player)
    await data_uno.set_data(state)

    if player.is_me:
        answer = _("Well, I have run out of my hand. I have to remain only an observer =(.")
    else:
        answer = _(
            "{user} puts his last card and leaves the game as the winner."
        ).format(user=user.mention_html())

    await state.bot.send_message(state.key.chat_id, answer)


async def kick_for_kick(
        state: FSMContext,
        timer: TimerTasks,
        data_uno: UnoData,
        user: types.User
):
    await data_uno.players.kick_player(state, data_uno.deck, data_uno.players(user.id))
    await data_uno.set_data(state)

    answer = _("{user} is kicked from the game for kick out of this chat.").format(user=user.mention_html())
    await state.bot.send_message(state.key.chat_id, answer)

    if len(data_uno.players) == 1:
        data_uno.settings.mode = UnoMode.FAST
        await finish(state, timer, data_uno)


async def kick_for_idle(
        message: types.Message,
        state: FSMContext,
        timer: TimerTasks,
        data_uno: UnoData,
        user: types.User
):
    await data_uno.players.kick_player(state, data_uno.deck, data_uno.players(user.id))
    await data_uno.set_data(state)

    answer = _("{user} is kicked from the game.").format(user=user.mention_html())
    await message.reply(answer)

    if len(data_uno.players) == 1:
        data_uno.settings.mode = UnoMode.FAST
        await finish(state, timer, data_uno)
