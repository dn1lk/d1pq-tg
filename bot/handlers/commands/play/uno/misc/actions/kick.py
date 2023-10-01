from typing import Callable

from aiogram import Bot, types
from aiogram.fsm.context import FSMContext
from aiogram.utils.i18n import gettext as _

from core.utils import TimerTasks
from .. import keyboards
from ..data import UnoData


async def kick_for_cards(
        bot: Bot,
        state: FSMContext,
        data_uno: UnoData,
        user: types.User
):
    data_uno.players.finish_player(user.id)
    await data_uno.set_data(state)

    player_data = data_uno.players.finished[user.id]

    if player_data.is_me:
        answer = _("Well, I have run out of my hand. I have to remain only an observer. 🫣")
    else:
        answer = _(
            "{user} puts last card and leaves the game as the winner."
        ).format(user=user.mention_html())

    await bot.send_message(state.key.chat_id, answer)


def kick(func: Callable[[types.User], str]):
    async def kick_decorator(
            bot: Bot,
            state: FSMContext,
            timer: TimerTasks,
            data_uno: UnoData,
            user: types.User,
    ):
        current_id = data_uno.players.current_id

        await data_uno.players.kick_player(state, data_uno.deck, user.id)

        answer = func(user)

        if user.id == current_id:
            answer_next = await data_uno.do_next(bot, state)
            message = await bot.send_message(
                state.key.chat_id, f'{answer}\n{answer_next}',
                reply_markup=keyboards.show_cards(bluffed=data_uno.state.bluffed)
            )

            from .turn import update_timer
            await update_timer(message, bot, state, timer, data_uno)
        else:
            await data_uno.set_data(state)
            await bot.send_message(state.key.chat_id, answer)

    return kick_decorator


@kick
def kick_for_kick(user: types.User):
    """Kick player from the game for kick from the chat"""

    return _("{user} is also kicked from the game.").format(user=user.mention_html())


@kick
def kick_for_idle(user: types.User):
    """Kick player from the game for idling"""

    return _("{user} is kicked from the game.").format(user=user.mention_html())
