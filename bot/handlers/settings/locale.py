from aiogram import Router, F, types, html
from aiogram.utils.i18n import I18n, gettext as _

from bot.utils.database.context import DataBaseContext
from .misc import keyboards as k

router = Router(name="settings:locale")
router.callback_query.filter(k.SettingsKeyboard.filter(F.action == 'locale'))


def get_locale_vars(locales: tuple) -> tuple[tuple[str, str], ...]:
    return tuple(zip(locales, ('English', 'Русский')))


@router.callback_query(k.SettingsKeyboard.filter(F.value))
async def locale_update_handler(
        query: types.CallbackQuery,
        i18n: I18n,
        callback_data: k.SettingsKeyboard,
        db: DataBaseContext,
):
    answer = _(
        "<b>The language has been successfully updated.</b>\n\n"
        "Already the next message will be in the language: {locale}."
    )
    await db.set_data(locale=callback_data.value)
    await query.message.edit_text(
        answer.format(locale=dict(get_locale_vars(i18n.available_locales))[callback_data.value])
    )
    await query.answer()


@router.callback_query()
async def locale_handler(query: types.CallbackQuery, i18n: I18n):
    locales = get_locale_vars(i18n.available_locales)
    answer = _(
        "<b>Update bot language.</b>\n\n"
        "Current language: {locale}. Available languages:"
    )

    await query.message.edit_text(
        answer.format(locale=html.bold(dict(locales)[i18n.current_locale])),
        reply_markup=k.locale(locales, i18n.current_locale)
    )
    await query.answer()
