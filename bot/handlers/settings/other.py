from aiogram import Router, Bot, F, types
from aiogram.utils.i18n import gettext as _

from bot import filters as f
from . import keyboards as k
from .. import get_username

router = Router(name='settings:other')


async def get_answer(chat_id: int, user_id: int, bot: Bot) -> dict:
    if chat_id == user_id:
        chat = _("dialogue")
    else:
        admins = ', '.join(get_username(admin.user) for admin in await bot.get_chat_administrators(chat_id))
        chat = _("chat - only for {admins}").format(
            admins=admins or _("only I don't know who it is... So")
        )

    return {
        'text': _("My settings for this {chat}:").format(chat=chat),
        'reply_markup': k.settings(),
    }


@router.callback_query(f.AdminFilter(is_admin=False))
async def no_admin_handler(query: types.CallbackQuery):
    await query.answer(_("Only for administrators."))


@router.callback_query(k.Settings.filter(F.name == 'back'))
async def query_handler(query: types.CallbackQuery, bot: Bot):
    await query.message.edit_text(**await get_answer(query.message.chat.id, query.from_user.id, bot))
    await query.answer()
