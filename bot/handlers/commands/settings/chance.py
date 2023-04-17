from aiogram import Router, F, types, flags, html
from aiogram.utils.i18n import gettext as _

from bot.core.utils import database
from . import SettingsActions, keyboards

router = Router(name="chance")
router.callback_query.filter(keyboards.SettingsData.filter(F.action == SettingsActions.CHANCE))


@router.callback_query(keyboards.SettingsData.filter(F.value))
async def update_handler(
        query: types.CallbackQuery,
        db: database.SQLContext,
        callback_data: keyboards.SettingsData,
):
    chance: int = callback_data.value
    await db.chance.set(query.message.chat.id, chance)

    answer = _(
        "<b>Text generation chance has been successfully updated.</b>\n"
        "Current chance: {chance}%."
    ).format(chance=html.bold(chance))

    await query.message.edit_text(answer)
    await query.answer()


@router.callback_query()
@flags.sql('chance')
async def start_handler(query: types.CallbackQuery, chance: int):
    answer = _(
        "<b>Update text generation chance.</b>\n"
        "Current chance: {chance}%.\n"
        "\n"
        "Available options:"
    ).format(chance=html.bold(chance))

    await query.message.edit_text(answer, reply_markup=keyboards.chance_keyboard(chance))
    await query.answer()
