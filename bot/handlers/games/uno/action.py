from aiogram import Bot, Router, types, flags
from aiogram.fsm.context import FSMContext

from bot.utils.database.context import DataBaseContext
from .process import UnoData
from .process.exceptions import UnoNoUsersException
from .process.core import finish

router = Router(name='game:uno:action')


@router.chat_member()
@flags.data('members')
async def on_member_leave_handler(
        event: types.ChatMemberUpdated,
        bot: Bot,
        db: DataBaseContext,
        state: FSMContext,
        members: list | None = None,
):
    data_uno: UnoData = UnoData(**(await state.get_data()).get('uno'))

    if event.new_chat_member.user.id in data_uno.users:
        try:
            await data_uno.remove_user(state, event.new_chat_member.user.id)
        except UnoNoUsersException:
            await finish(data_uno, state)

    from ... import action

    await action.leave_handler(event, bot, db, members)
