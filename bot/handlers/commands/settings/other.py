from aiogram import Router, Bot, F, types, enums
from aiogram.utils.i18n import gettext as _

from core import filters
from . import SettingsActions, keyboards
from .. import CommandTypes

router = Router(name='other')


async def get_answer(message: types.Message, bot: Bot) -> dict:
    if message.chat.type == enums.ChatType.PRIVATE:
        chat = _("dialogue")
    else:
        admins = ', '.join(admin.user.mention_html() for admin in await bot.get_chat_administrators(message.chat.id))
        chat = _("chat — only for {admins}").format(admins=admins or _("admins"))

    return {
        'text': _("My settings of this {chat}:").format(chat=chat),
        'reply_markup': keyboards.actions_keyboard(),
    }


@router.callback_query(keyboards.SettingsData.filter(F.action == SettingsActions.BACK))
async def back_handler(query: types.CallbackQuery, bot: Bot):
    message = query.message

    await message.edit_text(**await get_answer(message, bot))
    await query.answer()


@router.message(filters.Command(*CommandTypes.SETTINGS))
async def start_handler(message: types.Message, bot: Bot):
    await message.answer(**await get_answer(message, bot))
