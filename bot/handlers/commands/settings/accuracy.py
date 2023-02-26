from aiogram import Router, F, types, flags, html
from aiogram.utils.i18n import gettext as _

from bot.utils import database
from . import SettingsActions, keyboards

router = Router(name="accuracy")
router.callback_query.filter(keyboards.SettingsData.filter(F.action == SettingsActions.ACCURACY))


@router.callback_query(keyboards.SettingsData.filter(F.value))
async def update_handler(
        query: types.CallbackQuery,
        db: database.SQLContext,
        callback_data: keyboards.SettingsData,
):
    accuracy: int = callback_data.value
    await db.accuracy.set(query.message.chat.id, accuracy)

    answer = _(
        "<b>Text generation accuracy has been successfully updated.</b>\n"
        "Current accuracy: {accuracy}."
    ).format(accuracy=html.bold(accuracy))

    await query.message.edit_text(answer)
    await query.answer()


@router.callback_query()
@flags.sql('accuracy')
async def start_handler(query: types.CallbackQuery, accuracy: int):
    answer = _(
        "<b>Update text generation accuracy.</b>\n"
        "Current accuracy: {accuracy}.\n"
        "\n"
        "Available accuracy options:\n"
        "<i>More value - better, but longer generation, less - vice versa.</i>"
    ).format(accuracy=html.bold(accuracy))

    await query.message.edit_text(answer, reply_markup=keyboards.accuracy_keyboard(accuracy))
    await query.answer()
