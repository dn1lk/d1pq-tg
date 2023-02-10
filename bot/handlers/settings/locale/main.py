from functools import lru_cache

from aiogram import Router, F, types, html
from aiogram.utils.i18n import I18n, gettext as _

from . import keyboard as k
from ....utils import database

router = Router(name="settings:locale")
router.callback_query.filter()


@lru_cache(maxsize=2)
def transcript_locale(locale: str) -> str:
    match locale:
        case 'ru':
            return 'Russian'
        case 'en':
            return 'English'

    raise TypeError('Unknown locale')


@router.callback_query(k.SettingsKeyboard.filter(F.value))
async def update_handler(
        query: types.CallbackQuery,
        db: database.SQLContext,
        i18n: I18n,
        callback_data: k.SettingsKeyboard,
):
    locale = callback_data.value
    await db.locale.set(query.message.chat.id, locale)

    with i18n.use_locale(locale):
        answer = _(
            """
            <b>The language has been successfully updated.</b>\n
            Current language: {locale}.
            """
        ).format(locale=html.bold(transcript_locale(locale)))

        await query.message.edit_text(answer)
        await query.answer()


@router.callback_query(k.SettingsKeyboard.filter(F.action == k.SettingsAction.LOCALE))
async def start_handler(query: types.CallbackQuery, i18n: I18n):
    locales = {locale_code: transcript_locale(locale_code) for locale_code in i18n.available_locales}

    answer = _(
        """
        <b>Update bot language.</b>\n
        Current language: {locale}.\n
        \n
        Available languages:
        """
    ).format(locale=html.bold(locales[i18n.current_locale]))

    await query.message.edit_text(answer, reply_markup=k.locale(locales, i18n.current_locale))
    await query.answer()
