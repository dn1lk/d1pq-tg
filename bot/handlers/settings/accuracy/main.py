from aiogram import Router, F, types, flags, html
from aiogram.utils.i18n import gettext as _

from . import keyboard as k
from ....utils import database

router = Router(name="settings:accuracy")


@router.callback_query(k.SettingsKeyboard.filter(F.action == k.SettingsAction.ACCURACY))
@flags.data('accuracy')
async def start_handler(query: types.CallbackQuery, accuracy: int):
    answer = _(
        """
        <b>Update text generation accuracy.</b>\n
        Current accuracy: {accuracy}.\n
        \n
        Available accuracy options:\n
        <i>(More value - better, but longer generation, less - vice versa.)</i>
        """
    ).format(accuracy=html.bold(accuracy))

    await query.message.edit_text(answer, reply_markup=k.accuracy(accuracy))
    await query.answer()


@router.callback_query(k.AccuracyKeyboard.filter(F.value))
async def update_handler(
        query: types.CallbackQuery,
        callback_data: k.AccuracyKeyboard,
        db: database.SQLContext,
):
    accuracy = callback_data.value
    await db.accuracy.set(query.message.chat.id, accuracy)

    answer = _(
        """
        <b>Text generation accuracy has been successfully updated.</b>\n
        Current accuracy: {accuracy}%.
        """
    ).format(accuracy=html.bold(accuracy))

    await query.message.edit_text(answer)
    await query.answer()
