from aiogram import F, Router, types
from aiogram.utils import formatting
from aiogram.utils.i18n import I18n
from aiogram.utils.i18n import gettext as _

from utils import database
from utils.database.types import Utf8

from . import SettingsActions, keyboards
from .misc.helpers import transcript_locale

router = Router(name="locale")
router.callback_query.filter(keyboards.SettingsData.filter(F.action == SettingsActions.LOCALE))


@router.callback_query(keyboards.SettingsData.filter(F.value))
async def update_handler(
    query: types.CallbackQuery,
    i18n: I18n,
    callback_data: keyboards.SettingsData,
    main_settings: database.MainSettings,
) -> None:
    assert isinstance(query.message, types.Message), "wrong message"

    main_settings.locale = Utf8(callback_data.value)
    await main_settings.save()

    with i18n.use_locale(main_settings.locale):
        content = formatting.Text(
            formatting.Bold(_("The language has been successfully updated.")),
            "\n",
            _("Current language"),
            ": ",
            formatting.Bold(transcript_locale(main_settings.locale)),
            ".",
        )

    await query.message.edit_text(**content.as_kwargs())
    await query.answer()


@router.callback_query()
async def start_handler(query: types.CallbackQuery, i18n: I18n) -> None:
    assert isinstance(query.message, types.Message), "wrong message"

    locales = {locale_code: transcript_locale(locale_code) for locale_code in i18n.available_locales}

    content = formatting.Text(
        formatting.Bold(_("Change language")),
        ".\n",
        _("Current language"),
        ": ",
        formatting.Bold(locales[i18n.current_locale]),
        "\n\n",
        _("Available languages"),
        ":",
    )

    await query.message.edit_text(
        reply_markup=keyboards.locale_keyboard(locales, i18n.current_locale),
        **content.as_kwargs(),
    )

    await query.answer()
