from aiogram import Router, F, types
from aiogram.utils.i18n import gettext as _, lazy_gettext as __

from bot.core import filters
from .misc import keyboards

UPDATE = __("\n\nUpdate:")

router = Router(name='settings')


@router.callback_query(keyboards.SettingsData.filter(F.action), filters.IsAdmin(is_admin=False))
async def no_admin_handler(query: types.CallbackQuery):
    await query.answer(_("Only for administrators."))
