from aiogram import Router, Bot, F, types, flags, html
from aiogram.utils.i18n import gettext as _

from bot.utils.database.context import DataBaseContext
from . import UPDATE, UPDATE_AGAIN
from .misc import keyboards as k

router = Router(name="settings:chance")
router.callback_query.filter(k.SettingsKeyboard.filter(F.action == k.SettingsAction.CHANCE))


@router.callback_query(k.SettingsKeyboard.filter(F.value))
async def update_handler(
        query: types.CallbackQuery,
        callback_data: k.SettingsKeyboard,
        bot: Bot,
        db: DataBaseContext,
):
    if 5 < callback_data.value < 90:
        answer = _("Text generation chance successfully updated: {chance}%.")
    else:
        answer = _("Text generation chance has reached the limit: {chance}%, ")

        if callback_data.value <= 5:
            answer += _("below is impossible.")
        else:
            answer += _("higher is impossible.")

    await db.set_data(chance=callback_data.value * await bot.get_chat_member_count(query.message.chat.id) / 100)
    await query.message.edit_text(
        answer.format(chance=html.bold(callback_data.value)) + UPDATE_AGAIN.value,
        reply_markup=k.chance(callback_data.value)
    )
    await query.answer()


@router.callback_query()
@flags.data('chance')
async def start_handler(
        query: types.CallbackQuery,
        chance: float,
):
    await query.message.edit_text(
        _("Current text generation chance: {chance}%.").format(chance=html.bold(chance)) + UPDATE.value,
        reply_markup=k.chance(chance)
    )
    await query.answer()
