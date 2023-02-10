from aiogram import Router, Bot, F, types
from aiogram.utils.i18n import gettext as _

from . import keyboard as k
from .. import Commands
from ... import filters

router = Router(name='settings:other')


async def get_answer(message: types.Message, bot: Bot) -> dict:
    if message.chat.type == 'private':
        chat = _("dialogue")
    else:
        admins = ', '.join(str(admin.user) for admin in await bot.get_chat_administrators(message.chat.id))
        chat = _("chat - only for {admins}").format(admins=admins or _("admins"))

    return {
        'text': _("My settings of this {chat}:").format(chat=chat),
        'reply_markup': k.settings(),
    }


@router.callback_query(k.SettingsKeyboard.filter(F.action == k.SettingsAction.BACK))
async def back_handler(query: types.CallbackQuery, bot: Bot):
    message = query.message

    await message.edit_text(**await get_answer(message, bot))
    await query.answer()


@router.message(filters.Command(Commands.SETTINGS.value))
async def settings_handler(message: types.Message, bot: Bot):
    await message.answer(**await get_answer(message, bot))
