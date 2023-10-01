from functools import lru_cache

from aiogram import Router, F, types, html
from aiogram.utils.i18n import I18n, gettext as _

from core.utils import database
from . import SettingsActions, keyboards

router = Router(name="locale")
router.callback_query.filter(keyboards.SettingsData.filter(F.action == SettingsActions.LOCALE))


@lru_cache(maxsize=2)
def transcript_locale(locale: str) -> str:
    match locale:
        case 'ru':
            return 'Русский'
        case 'en':
            return 'English'

    raise TypeError(f'Unknown locale: {locale}')


@router.callback_query(keyboards.SettingsData.filter(F.value))
async def update_handler(
        query: types.CallbackQuery,
        i18n: I18n,
        callback_data: keyboards.SettingsData,
        main_settings: database.MainSettings,
):
    main_settings.locale = callback_data.value
    await main_settings.save()

    with i18n.use_locale(main_settings.locale):
        answer = _(
            "<b>The language has been successfully updated.</b>\n"
            "Current language: {locale}."
        ).format(locale=html.bold(transcript_locale(main_settings.locale)))

    await query.message.edit_text(answer)
    await query.answer()


@router.callback_query()
async def start_handler(query: types.CallbackQuery, i18n: I18n):
    locales = {
        locale_code: transcript_locale(locale_code)
        for locale_code in i18n.available_locales
    }

    answer = _(
        "<b>Update bot language.</b>\n"
        "Current language: {locale}.\n"
        "\n"
        "Available languages:"
    ).format(locale=html.bold(locales[i18n.current_locale]))

    await query.message.edit_text(answer, reply_markup=keyboards.locale_keyboard(locales, i18n.current_locale))
    await query.answer()
