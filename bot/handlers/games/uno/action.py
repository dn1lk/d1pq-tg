from aiogram import Router, F, types, flags
from aiogram.fsm.context import FSMContext

from bot.utils.database.context import DataBaseContext
from .data import UnoData
from .exceptions import UnoNoUsersException
from .process import finish

router = Router(name='game:uno:action')


@router.message(F.content_type == types.ContentType.LEFT_CHAT_MEMBER)
@flags.data('members')
async def on_member_leave_handler(
        message: types.Message,
        db: DataBaseContext,
        state: FSMContext,
        members: list | None = None,
):
    data_uno: UnoData = UnoData(**(await state.get_data()).get('uno'))

    if message.left_chat_member.id in data_uno.users:
        try:
            await data_uno.remove_user(state, message.left_chat_member.id)
        except UnoNoUsersException:
            await finish(message, data_uno, state)

    from ... import action

    await action.on_member_leave_handler(message, db, members)
