from aiogram import Router, F, types, flags
from aiogram.fsm.context import FSMContext

from bot.utils.database.context import DataBaseContext
from .process import UnoData
from .process.middleware import UnoDataMiddleware
from ...transitions.group import my_admin_filter, remove_member

router = Router(name='game:uno:action')
router.message.outer_middleware(UnoDataMiddleware())
router.chat_member.outer_middleware(UnoDataMiddleware())


@router.chat_member()
@flags.data('members')
async def leave_handler(
        event: types.ChatMemberUpdated,
        db: DataBaseContext,
        state: FSMContext,
        data_uno: UnoData,
        members: list | None = None,
):
    if event.new_chat_member.user.id in data_uno.users:
        from .process.core import kick_for_kick
        await kick_for_kick(state, data_uno, event.new_chat_member.user)

    await remove_member(db, members, event.new_chat_member.user.id)


@router.message(F.left_chat_member, my_admin_filter)
@flags.data('members')
async def leave_message_handler(
        message: types.Message,
        state: FSMContext,
        db: DataBaseContext,
        data_uno: UnoData,
        members: list | None = None,
):
    if message.left_chat_member.id in data_uno.users:
        from .process.core import kick_for_kick
        await kick_for_kick(state, data_uno, message.left_chat_member)

    await remove_member(db, members, message.left_chat_member.id)
