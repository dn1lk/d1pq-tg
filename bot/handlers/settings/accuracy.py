from aiogram import Router, F, types, flags, html
from aiogram.utils.i18n import gettext as _

from bot.utils.database.context import DataBaseContext
from . import UPDATE, UPDATE_AGAIN, keyboards as k

router = Router(name="settings:accuracy")
router.callback_query.filter(k.Settings.filter(F.name == 'accuracy'))


@router.callback_query(k.Settings.filter(F.value))
async def accuracy_update_handler(
        query: types.CallbackQuery,
        callback_data: k.Settings,
        db: DataBaseContext,
):
    accuracy = int(callback_data.value)
    answer = _("Text generation accuracy updated successfully: {accuracy}.")

    await db.set_data(accuracy=accuracy)
    await query.message.edit_text(
        answer.format(accuracy=html.bold(accuracy)) + UPDATE_AGAIN.value,
        reply_markup=k.accuracy(accuracy)
    )
    await query.answer()


@router.callback_query()
@flags.data('accuracy')
async def accuracy_handler(
        query: types.CallbackQuery,
        accuracy: int,
):
    answer = _(
        "Current text generation accuracy: {accuracy}.\n\n"
        "The larger the value, the more accurate, but the text generation will take longer."
    )

    await query.message.edit_text(
        answer.format(accuracy=html.bold(accuracy)) + UPDATE.value,
        reply_markup=k.accuracy(accuracy)
    )
    await query.answer()
