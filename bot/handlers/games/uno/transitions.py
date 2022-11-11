from aiogram import Router, F, types, flags
from aiogram.fsm.context import FSMContext

from bot.utils.database.context import DataBaseContext
from .misc import UnoData
from .. import Games
from ...transitions.group import my_admin_filter, remove_member

router = Router(name='game:uno:transition')

router.chat_member.filter(Games.UNO)
router.message.filter(Games.UNO)


async def kick_user(db: DataBaseContext, state: FSMContext, user: types.User, members: list | None):
    data_uno = await UnoData.get_data(state)

    if user.id in data_uno.users:
        from .misc.process import kick_for_kick
        await kick_for_kick(state, data_uno, user)

    await remove_member(db, members, user.id)


@router.chat_member()
@flags.data('members')
async def leave_handler(
        event: types.ChatMemberUpdated,
        db: DataBaseContext,
        state: FSMContext,
        members: list | None = None,
):
    await kick_user(db, state, event.new_chat_member.user, members)


@router.message(F.left_chat_member, my_admin_filter)
@flags.data('members')
async def leave_message_handler(
        message: types.Message,
        state: FSMContext,
        db: DataBaseContext,
        members: list | None = None,
):
    await kick_user(db, state, message.left_chat_member, members)
