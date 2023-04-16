from aiogram import Bot, Router, F, flags, filters, types
from aiogram.fsm.context import FSMContext

from bot.core.utils import database, TimerTasks
from bot.handlers.transitions.group import my_is_not_admin_filter, remove_member
from .misc.actions.base import finish, restart
from .misc.actions.kick import kick_for_kick
from .misc.data import UnoData
from .misc.data.settings.modes import UnoMode
from .. import PlayStates

router = Router(name='play:uno:transition')

router.chat_member.filter(PlayStates.UNO)
router.message.filter(PlayStates.UNO, my_is_not_admin_filter)


async def kick_user(
        bot: Bot,
        db: database.SQLContext,
        state: FSMContext,
        timer: TimerTasks,
        members: list | None,
        user: types.User,
):
    data_uno = await UnoData.get_data(state)

    if user.id in data_uno.players.playing:
        await kick_for_kick(bot, state, timer, data_uno, user)

        if len(data_uno.players) == 1:
            await finish(bot, state, timer, data_uno)
        elif len(data_uno.players.playing) == 1 and data_uno.settings.mode is UnoMode.WITH_POINTS:
            await restart(bot, state, timer, data_uno)

    await remove_member(db, members, state.key.chat_id, user.id)


@router.chat_member(filters.ChatMemberUpdatedFilter(filters.LEAVE_TRANSITION))
@flags.timer(name='play', cancelled=False)
@flags.sql('members')
async def leave_action_handler(
        event: types.ChatMemberUpdated,
        bot: Bot,
        db: database.SQLContext,
        state: FSMContext,
        timer: TimerTasks,
        members: list[int] = None,
):
    await kick_user(bot, db, state, timer, members, event.new_chat_member.user)


@router.message(F.left_chat_member)
@flags.timer(name='play', cancelled=False)
@flags.sql('members')
async def leave_message_handler(
        message: types.Message,
        bot: Bot,
        db: database.SQLContext,
        state: FSMContext,
        timer: TimerTasks,
        members: list[int] = None,
):
    await kick_user(bot, db, state, timer, members, message.left_chat_member)
