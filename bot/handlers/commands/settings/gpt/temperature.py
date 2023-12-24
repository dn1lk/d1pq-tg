from aiogram import Router, F, types, html, flags
from aiogram.utils.i18n import gettext as _

from core.utils import database
from . import GPTOptionsActions, keyboards

router = Router(name="gpt:temperature")
router.callback_query.filter(keyboards.GPTOptionsData.filter(F.action == GPTOptionsActions.TEMPERATURE))


@router.callback_query(keyboards.GPTOptionsData.filter(F.value))
@flags.database('gpt_settings')
async def update_handler(
        query: types.CallbackQuery,
        callback_data: keyboards.GPTOptionsData,
        gpt_settings: database.GPTSettings
):
    gpt_settings.temperature = int(callback_data.value) / 10
    await gpt_settings.save()

    answer = _(
        "<b>Text generation temperature has been successfully updated.</b>\n"
        "Current temperature: {temperature}."
    ).format(temperature=html.bold(round(gpt_settings.temperature, 2)))

    await query.message.edit_text(answer)
    await query.answer()


@router.callback_query()
@flags.database('gpt_settings')
async def start_handler(query: types.CallbackQuery, gpt_settings: database.GPTSettings):
    answer = _(
        "<b>Update text generation temperature.</b>\n"
        "Current temperature: {temperature}.\n"
        "\n"
        "Available options:"
    ).format(temperature=html.bold(round(gpt_settings.temperature, 2)))

    await query.message.edit_text(answer, reply_markup=keyboards.temperature_keyboard(gpt_settings.temperature))
    await query.answer()
