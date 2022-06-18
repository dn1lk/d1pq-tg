from aiogram import Router, Bot, F, types
from aiogram.utils.i18n import gettext as _

from bot import filters as f, keyboards as k

from .. import get_username

router = Router(name='settings:other')


async def get_answer(chat_id: int, user_id: int, bot: Bot) -> dict:
    if chat_id == user_id:
        chat = _("dialogue")
    else:
        chat = _("chat - they are only available to the administrator - {admins}").format(
            admins=', '.join(
                map(
                    lambda admin: get_username(admin.user),
                    await bot.get_chat_administrators(chat_id)
                )
            ) or _("only I don't know who it is... So")
        )

    return {
        'text': _("My settings for this {chat}:").format(chat=chat),
        'reply_markup': k.settings(),
    }


@router.callback_query(f.AdminFilter(is_admin=False))
async def no_admin_handler(query: types.CallbackQuery):
    return query.answer(_("These commands are only available to the administrator."))


@router.callback_query(k.Settings.filter(F.name == 'back'))
async def query_handler(query: types.CallbackQuery, bot: Bot):
    await query.message.edit_text(**await get_answer(query.message.chat.id, query.from_user.id, bot))
