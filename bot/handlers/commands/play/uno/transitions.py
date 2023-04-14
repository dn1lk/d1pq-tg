from aiogram import Router, F, flags, filters, types
from aiogram.fsm.context import FSMContext

from bot.core.utils import TimerTasks
from bot.core.utils import database
from bot.handlers.transitions.group import my_is_not_admin_filter, remove_member
from .misc.data import UnoData
from .. import PlayStates

router = Router(name='play:uno:transition')

router.chat_member.filter(PlayStates.UNO)
router.message.filter(PlayStates.UNO, my_is_not_admin_filter)


async def kick_user(db: database.SQLContext, state: FSMContext, user: types.User, members: list | None):
    data_uno = await UnoData.get_data(state)

    if data_uno.players(user.id):
        timer = TimerTasks('play')

        from .misc.actions.kick import kick_for_kick
        await kick_for_kick(state, timer, data_uno, user)

    await remove_member(db, members, state.key.chat_id, user.id)


@router.chat_member(filters.ChatMemberUpdatedFilter(filters.LEAVE_TRANSITION))
@flags.sql('members')
async def leave_action_handler(
        event: types.ChatMemberUpdated,
        db: database.SQLContext,
        state: FSMContext,
        members: list[int] = None,
):
    await kick_user(db, state, event.new_chat_member.user, members)


@router.message(F.left_chat_member)
@flags.sql('members')
async def leave_message_handler(
        message: types.Message,
        state: FSMContext,
        db: database.SQLContext,
        members: list[int] = None,
):
    await kick_user(db, state, message.left_chat_member, members)
