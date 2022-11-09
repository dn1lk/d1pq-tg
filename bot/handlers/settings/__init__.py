from aiogram import Router, Bot, F, types
from aiogram.fsm.state import StatesGroup, State
from aiogram.utils.i18n import gettext as _
from aiogram.utils.i18n import lazy_gettext as __

from bot import filters as f
from .misc import keyboards as k
from .. import get_username


class Settings(StatesGroup):
    command = State()


UPDATE = __("\n\nUpdate:")
UPDATE_AGAIN = __("\n\nUpdate again:")

router = Router(name='settings')


@router.callback_query(f.AdminFilter(is_admin=False))
async def no_admin_handler(query: types.CallbackQuery):
    await query.answer(_("Only for administrators."))


async def get_setup_answer(message: types.Message, bot: Bot) -> dict:
    if message.chat.type == 'private':
        chat = _("dialogue")
    else:
        admins = ', '.join(get_username(admin.user) for admin in await bot.get_chat_administrators(message.chat.id))
        chat = _("chat - only for {admins}").format(admins=admins or _("admins"))

    return {
        'text': _("My settings of this {chat}:").format(chat=chat),
        'reply_markup': k.settings(),
    }


@router.callback_query(k.SettingsKeyboard.filter(F.action == k.SettingsAction.BACK))
async def back_handler(query: types.CallbackQuery, bot: Bot):
    await query.message.edit_text(**await get_setup_answer(query.message, bot))
    await query.answer()


def setup():
    from .accuracy import router as accuracy_rt
    from .chance import router as chance_rt
    from .locale import router as locale_rt

    sub_routers = (
        accuracy_rt,
        chance_rt,
        locale_rt,
    )

    for sub_router in sub_routers:
        router.include_router(sub_router)

    from .commands import setup as command_st
    from .record import setup as record_st

    command_st(router)
    record_st(router)

    return router
