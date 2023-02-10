from random import choice

from aiogram import Bot, Router, filters, types
from aiogram.utils.i18n import gettext as _


router = Router(name='transitions:private')


@router.my_chat_member(filters.ChatMemberUpdatedFilter(filters.KICKED >> filters.MEMBER))
async def my_return_handler(event: types.ChatMemberUpdated, bot: Bot):
    answer = (
        _("Wait, was I kicked, {user}?"),
        _("Oh, wait. I already wrote this to you..."),
        _("I am with you again, {user}!"),
        _("Oh, {user}, I got out of your anger?"),
        _("Ha! I returned, {user}!"),
    )

    await bot.send_message(event.chat.id, choice(answer).format(user=event.from_user))
