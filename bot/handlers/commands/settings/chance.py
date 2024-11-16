from aiogram import F, Router, flags, types
from aiogram.utils import formatting
from aiogram.utils.i18n import gettext as _

from utils import database
from utils.database.types import Float

from . import SettingsActions, keyboards

router = Router(name="chance")
router.callback_query.filter(keyboards.SettingsData.filter(F.action == SettingsActions.CHANCE))


@router.callback_query(keyboards.SettingsData.filter(F.value))
@flags.database("gen_settings")
async def update_handler(
    query: types.CallbackQuery,
    callback_data: keyboards.SettingsData,
    gen_settings: database.GenSettings,
) -> None:
    assert isinstance(query.message, types.Message), "wrong message"
    assert isinstance(callback_data.value, str), "wrong callback data"

    gen_settings.chance = Float(int(callback_data.value) / 100)
    await gen_settings.save()

    content = formatting.Text(
        formatting.Bold(_("Text generation chance has been successfully updated.")),
        "\n",
        _("Current chance"),
        ": ",
        formatting.Bold(int(gen_settings.chance * 100)),
        "%.",
    )

    await query.message.edit_text(**content.as_kwargs())
    await query.answer()


@router.callback_query()
@flags.database("gen_settings")
async def start_handler(query: types.CallbackQuery, gen_settings: database.GenSettings) -> None:
    assert isinstance(query.message, types.Message), "wrong message"

    content = formatting.Text(
        formatting.Bold(_("Change text generation chance")),
        ".\n",
        _("Current chance"),
        ": ",
        formatting.Bold(int(gen_settings.chance * 100)),
        "%.\n\n",
        _("Available options"),
        ":",
    )

    await query.message.edit_text(
        reply_markup=keyboards.chance_keyboard(int(gen_settings.chance * 100)),
        **content.as_kwargs(),
    )

    await query.answer()
