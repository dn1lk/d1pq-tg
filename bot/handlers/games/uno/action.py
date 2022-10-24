from aiogram import Bot, Router, types, flags
from aiogram.fsm.context import FSMContext
from aiogram.utils.i18n import gettext as _

from bot.utils.database.context import DataBaseContext
from .process import UnoData
from .process.exceptions import UnoNoUsersException
from .process.core import finish
from .process.middleware import UnoDataMiddleware

router = Router(name='game:uno:action')
router.chat_member.outer_middleware(UnoDataMiddleware())


@router.chat_member()
@flags.data('members')
@flags.uno
async def leave_handler(
    event: types.ChatMemberUpdated,
    bot: Bot,
    db: DataBaseContext,
    state: FSMContext,
    data_uno: UnoData,
    members: list | None = None,
):
    if event.new_chat_member.user.id in data_uno.users:
        message = await bot.send_message(
            event.chat.id,
            _("{user} was kicked from the game for kick out of this chat.").format(user=event.new_chat_member.user))

        try:
            await data_uno.remove_user(state, event.new_chat_member.user.id)
        except UnoNoUsersException:
            await finish(message, data_uno, state)

    from ... import action

    await action.leave_handler(event, bot, db, members)
