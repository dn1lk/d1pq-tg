from aiogram import Router, Bot, F, types
from aiogram.utils.i18n import gettext as _

from worker import filters as f, keyboards as k
from worker.handlers import USERNAME

router = Router(name='settings_other')


@router.callback_query(f.AdminFilter(is_admin=False))
async def settings_no_admin_handler(callback_query: types.CallbackQuery):
    return callback_query.answer(_("These commands are only available to the administrator."))


async def get_settings_answer(chat_id: int, user_id: int, bot: Bot) -> dict:
    if chat_id == user_id:
        chat = _("dialogue")
    else:
        chat = _("chat - they are only available to the administrator - {admins}").format(
            admins=', '.join(
                map(
                    lambda admin: USERNAME.format(
                        id=admin.user.id,
                        name=admin.user.first_name
                    ),
                    await bot.get_chat_administrators(chat_id)
                )
            ) or _("only I don't know who it is... So")
        )

    return {
        'text': _("My settings for this {chat}:").format(chat=chat),
        'reply_markup': k.settings(),
    }


@router.callback_query(k.SettingsData.filter(F.name == 'back'))
async def settings_query_handler(query: types.CallbackQuery, bot: Bot):
    await query.message.edit_text(**await get_settings_answer(query.message.chat.id, query.from_user.id, bot))
