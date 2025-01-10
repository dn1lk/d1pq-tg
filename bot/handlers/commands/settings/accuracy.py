from aiogram import F, Router, flags, types
from aiogram.utils import formatting
from aiogram.utils.i18n import gettext as _

from utils import database
from utils.database.types import Uint8

from . import SettingsActions, keyboards

router = Router(name="temperature")
router.callback_query.filter(keyboards.SettingsData.filter(F.action == SettingsActions.ACCURACY))


@router.callback_query(keyboards.SettingsData.filter(F.value))
@flags.database("gen_settings")
async def update_handler(
    query: types.CallbackQuery,
    callback_data: keyboards.SettingsData,
    gen_settings: database.GenSettings,
) -> None:
    assert isinstance(query.message, types.Message), "wrong message"
    assert isinstance(callback_data.value, str), "wrong callback data"

    gen_settings.accuracy = Uint8(callback_data.value)
    await gen_settings.save()

    content = formatting.Text(
        formatting.Bold(_("Text generation accuracy has been successfully updated.")),
        "\n",
        _("Current accuracy"),
        ": ",
        formatting.Bold(int(gen_settings.accuracy)),
        ".",
    )

    await query.message.edit_text(**content.as_kwargs())
    await query.answer()


@router.callback_query()
@flags.database("gen_settings")
async def start_handler(query: types.CallbackQuery, gen_settings: database.GenSettings) -> None:
    assert isinstance(query.message, types.Message), "wrong message"

    content = formatting.Text(
        formatting.Bold(_("Change text generation accuracy.")),
        "\n",
        _("Current accuracy"),
        ": ",
        formatting.Bold(int(gen_settings.accuracy)),
        ".\n\n",
        _("Available options"),
        ":\n",
        formatting.Italic(_("The higher the value, the more usual the generation will be.")),
    )

    await query.message.edit_text(
        reply_markup=keyboards.accuracy_keyboard(gen_settings.accuracy),
        **content.as_kwargs(),
    )

    await query.answer()
