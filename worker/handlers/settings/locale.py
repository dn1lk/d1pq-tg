from typing import Optional

from aiogram import Router, Bot, F, types
from aiogram.dispatcher.fsm.context import FSMContext
from aiogram.utils.i18n import I18n, gettext as _

from worker import keyboards as k

router = Router(name="settings_locale")
router.callback_query.filter(k.SettingsData.filter(F.name == 'locale'))


@router.callback_query(k.SettingsData.filter(F.value))
async def settings_locale_two_handler(
        query: types.CallbackQuery,
        bot: Bot,
        i18n: I18n,
        callback_data: k.SettingsData,
        state: Optional[FSMContext] = None,
):
    await bot.sql.set_data(query.message.chat.id, 'locales', callback_data.value, state)
    await query.message.edit_text(
        _(
            "<b>The language has been successfully updated.</b>\n\n"
            "Already the next message will be in the language: {locale}."
        ).format(locale=dict(k.get_locale_var(i18n.available_locales))[callback_data.value])
    )


@router.callback_query()
async def settings_locale_one_handler(query: types.CallbackQuery, i18n: I18n):
    await query.message.edit_text(
        text=_("<b>Update bot language.</b>\n\nCurrent language: <b>{locale}</b>. Available languages:").format(
            locale=dict(k.get_locale_var(i18n.available_locales))[i18n.current_locale]
        ),
        reply_markup=k.locale(i18n)
    )
