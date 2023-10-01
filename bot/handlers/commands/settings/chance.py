from aiogram import Router, F, types, html, flags
from aiogram.utils.i18n import gettext as _

from core.utils import database
from . import SettingsActions, keyboards

router = Router(name="chance")
router.callback_query.filter(keyboards.SettingsData.filter(F.action == SettingsActions.CHANCE))


@router.callback_query(keyboards.SettingsData.filter(F.value))
@flags.database('gen_settings')
async def update_handler(
        query: types.CallbackQuery,
        callback_data: keyboards.SettingsData,
        gen_settings: database.GenSettings
):
    gen_settings.chance = int(callback_data.value) / 100
    await gen_settings.save()

    answer = _(
        "<b>Text generation chance has been successfully updated.</b>\n"
        "Current chance: {chance}%."
    ).format(chance=html.bold(int(gen_settings.chance * 100)))

    await query.message.edit_text(answer)
    await query.answer()


@router.callback_query()
@flags.database('gen_settings')
async def start_handler(query: types.CallbackQuery, gen_settings: database.GenSettings):
    answer = _(
        "<b>Update text generation chance.</b>\n"
        "Current chance: {chance}%.\n"
        "\n"
        "Available options:"
    ).format(chance=html.bold(int(gen_settings.chance * 100)))

    await query.message.edit_text(answer, reply_markup=keyboards.chance_keyboard(int(gen_settings.chance * 100)))
    await query.answer()
