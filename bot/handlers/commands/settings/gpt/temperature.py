from aiogram import F, Router, flags, types
from aiogram.utils import formatting
from aiogram.utils.i18n import gettext as _

from utils import database
from utils.database.types import Float

from . import GPTOptionsActions, keyboards

router = Router(name="gpt:temperature")
router.callback_query.filter(keyboards.GPTOptionsData.filter(F.action == GPTOptionsActions.TEMPERATURE))


@router.callback_query(keyboards.GPTOptionsData.filter(F.value))
@flags.database("gpt_settings")
async def update_handler(
    query: types.CallbackQuery,
    callback_data: keyboards.GPTOptionsData,
    gpt_settings: database.GPTSettings,
) -> None:
    assert isinstance(query.message, types.Message), "wrong message"
    assert callback_data.value is not None, "wrong callback data"

    gpt_settings.temperature = Float(int(callback_data.value) / 10)
    await gpt_settings.save()

    content = formatting.Text(
        formatting.Bold(_("Text generation temperature has been successfully updated.")),
        "\n",
        _("Current temperature"),
        ": ",
        formatting.Bold(round(gpt_settings.temperature, 2)),
        ".",
    )

    await query.message.edit_text(**content.as_kwargs())
    await query.answer()


@router.callback_query()
@flags.database("gpt_settings")
async def start_handler(query: types.CallbackQuery, gpt_settings: database.GPTSettings) -> None:
    assert isinstance(query.message, types.Message), "wrong message"

    content = formatting.Text(
        formatting.Bold(_("Change text generation temperature.")),
        "\n",
        _("Current temperature"),
        ": ",
        formatting.Bold(round(gpt_settings.temperature, 2)),
        "\n",
        _("Available options"),
        ":",
    )

    await query.message.edit_text(
        reply_markup=keyboards.temperature_keyboard(gpt_settings.temperature),
        **content.as_kwargs(),
    )

    await query.answer()
