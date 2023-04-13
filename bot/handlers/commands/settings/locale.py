from functools import lru_cache

from aiogram import Router, F, types, html
from aiogram.utils.i18n import gettext as _, I18n

from bot.core.utils import database
from . import SettingsActions, keyboards

router = Router(name="locale")
router.callback_query.filter(keyboards.SettingsData.filter(F.action == SettingsActions.LOCALE))


@lru_cache(maxsize=2)
def transcript_locale(locale: str) -> str:
    match locale:
        case 'ru':
            return 'Russian'
        case 'en':
            return 'English'

    raise TypeError('Unknown locale')


@router.callback_query(keyboards.SettingsData.filter(F.value))
async def update_handler(
        query: types.CallbackQuery,
        db: database.SQLContext,
        i18n: I18n,
        callback_data: keyboards.SettingsData,
):
    locale: str = callback_data.value
    await db.locale.set(query.message.chat.id, locale)

    with i18n.use_locale(locale):
        answer = _(
            "<b>The language has been successfully updated.</b>\n"
            "Current language: {locale}."
        ).format(locale=html.bold(transcript_locale(locale)))

    await query.message.edit_text(answer)
    await query.answer()


@router.callback_query()
async def start_handler(query: types.CallbackQuery, i18n: I18n):
    locales = {locale_code: transcript_locale(locale_code) for locale_code in i18n.available_locales}

    answer = _(
        "<b>Update bot language.</b>\n"
        "Current language: {locale}.\n"
        "\n"
        "Available languages:"
    ).format(locale=html.bold(locales[i18n.current_locale]))

    await query.message.edit_text(answer, reply_markup=keyboards.locale_keyboard(locales, i18n.current_locale))
    await query.answer()
