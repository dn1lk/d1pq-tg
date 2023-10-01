from aiogram import Router, F, types, html, flags
from aiogram.utils.i18n import gettext as _

from core.utils import database
from . import SettingsActions, keyboards

router = Router(name="temperature")
router.callback_query.filter(keyboards.SettingsData.filter(F.action == SettingsActions.ACCURACY))


@router.callback_query(keyboards.SettingsData.filter(F.value))
@flags.database('gen_settings')
async def update_handler(
        query: types.CallbackQuery,
        callback_data: keyboards.SettingsData,
        gen_settings: database.GenSettings
):
    gen_settings.accuracy = int(callback_data.value)
    await gen_settings.save()

    answer = _(
        "<b>Text generation accuracy has been successfully updated.</b>\n"
        "Current accuracy: {accuracy}."
    ).format(accuracy=html.bold(gen_settings.accuracy))

    await query.message.edit_text(answer)
    await query.answer()


@router.callback_query()
@flags.database('gen_settings')
async def start_handler(query: types.CallbackQuery, gen_settings: database.GenSettings):
    answer = _(
        "<b>Update text generation accuracy.</b>\n"
        "Current accuracy: {accuracy}.\n"
        "\n"
        "Available options:\n"
        "<i>The higher the value, the more usual the generation will be.</i>"
    ).format(accuracy=html.bold(gen_settings.accuracy))

    await query.message.edit_text(answer, reply_markup=keyboards.accuracy_keyboard(gen_settings.accuracy))
    await query.answer()
