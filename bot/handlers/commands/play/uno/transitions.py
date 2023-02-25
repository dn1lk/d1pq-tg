from aiogram import Router, F, flags, filters
from aiogram.fsm.context import FSMContext

from .misc import UnoData
from .. import Games
from ...transitions.group import my_not_admin_filter, remove_member

router = Router(name='game:uno:transition')

router.chat_member.filter(Games.UNO)
router.message.filter(Games.UNO, my_not_admin_filter)


async def kick_user(db: DataBaseContext, state: FSMContext, user: types.User, members: list | None):
    data_uno = await UnoData.get_data(state)

    if user.id in data_uno.users:
        from .misc.process import kick_for_kick
        await kick_for_kick(state, data_uno, user)

    await remove_member(db, members, user.id)


@router.chat_member(filters.ChatMemberUpdatedFilter(filters.LEAVE_TRANSITION))
@flags.data('members')
async def leave_action_handler(
        event: types.ChatMemberUpdated,
        db: DataBaseContext,
        state: FSMContext,
        members: list[int] = None,
):
    await kick_user(db, state, event.new_chat_member.user, members)


@router.message(F.left_chat_member)
@flags.data('members')
async def leave_message_handler(
        message: types.Message,
        state: FSMContext,
        db: DataBaseContext,
        members: list[int] = None,
):
    await kick_user(db, state, message.left_chat_member, members)
