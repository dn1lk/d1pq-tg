from aiogram import Router, F, types
from aiogram.utils.i18n import I18n, gettext as _

from bot.utils.database.context import DataBaseContext
from . import keyboards as k

router = Router(name="settings:locale")
router.callback_query.filter(k.Settings.filter(F.name == 'locale'))


@router.callback_query(k.Settings.filter(F.value))
async def locale_update_handler(
        query: types.CallbackQuery,
        i18n: I18n,
        callback_data: k.Settings,
        db: DataBaseContext,
):
    answer = _(
        "<b>The language has been successfully updated.</b>\n\n"
        "Already the next message will be in the language: {locale}."
    )
    await db.set_data(locale=callback_data.value)
    await query.message.edit_text(
        answer.format(locale=dict(k.get_locale_vars(i18n.available_locales))[callback_data.value])
    )
    await query.answer()


@router.callback_query()
async def locale_handler(query: types.CallbackQuery, i18n: I18n):
    answer = _(
        "<b>Update bot language.</b>\n\n"
        "Current language: <b>{locale}</b>. Available languages:"
    )
    await query.message.edit_text(
        answer.format(locale=dict(k.get_locale_vars(i18n.available_locales))[i18n.current_locale]),
        reply_markup=k.locale(i18n)
    )
    await query.answer()
