from aiogram import Router, F, types, flags, html
from aiogram.utils.i18n import gettext as _

from . import keyboard as k
from ....utils import database

router = Router(name="settings:chance")


@router.callback_query(k.ChanceKeyboard.filter(F.value))
async def update_handler(
        query: types.CallbackQuery,
        callback_data: k.SettingsKeyboard,
        db: database.SQLContext,
):
    chance = callback_data.value
    await db.chance.set(query.message.chat.id, chance)

    answer = _(
        """
        <b>Text generation chance has been successfully updated.</b>\n
        Current chance: {chance}%.
        """
    ).format(chance=html.bold(chance))

    await query.message.edit_text(answer)
    await query.answer()


@router.callback_query(k.SettingsKeyboard.filter(F.action == k.SettingsAction.CHANCE))
@flags.data('chance')
async def start_handler(query: types.CallbackQuery, chance: float):
    answer = _(
        """
        <b>Update text generation chance.</b>\n
        Current chance: {chance}.\n
        \n
        Available chance options:
        """
    ).format(chance=html.bold(chance))

    await query.message.edit_text(answer, reply_markup=k.chance(chance))
    await query.answer()
