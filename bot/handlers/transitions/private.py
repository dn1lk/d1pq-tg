from random import choice

from aiogram import Router, filters, types, Bot, F
from aiogram.utils.i18n import gettext as _

from .. import get_username

router = Router(name='transitions:private')
router.my_chat_member.filter(F.chat.type == 'private')


@router.my_chat_member(filters.ChatMemberUpdatedFilter(filters.KICKED >> filters.MEMBER))
async def my_return_handler(event: types.ChatMemberUpdated, bot: Bot):
    answer = (
        _("I am with you again, {user}!"),
        _("{user}, I got out of your anger?"),
        _("I returned, {user}!"),
    )

    await bot.send_message(event.chat.id, choice(answer).format(chat_title=get_username(event.from_user)))
