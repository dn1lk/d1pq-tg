from aiogram import Router, Bot, F, types, flags, html
from aiogram.utils.i18n import gettext as _

from bot.utils.database.context import DataBaseContext
from . import UPDATE, UPDATE_AGAIN
from .misc import keyboards as k

router = Router(name="settings:chance")
router.callback_query.filter(k.SettingsKeyboard.filter(F.action == 'chance'))


@router.callback_query(k.SettingsKeyboard.filter(F.value))
async def chance_update_handler(
        query: types.CallbackQuery,
        callback_data: k.SettingsKeyboard,
        bot: Bot,
        db: DataBaseContext,
):
    chance = float(callback_data.value)

    if 10 < chance < 90:
        answer = _("Text generation chance successfully updated: {chance}%.")
    else:
        answer = _("Text generation chance has reached the limit: {chance}%, ")

        if chance <= 10:
            answer += _("below is impossible.")
        else:
            answer += _("higher is impossible.")

    await db.set_data(chance=chance * await bot.get_chat_member_count(query.message.chat.id) / 100)
    await query.message.edit_text(
        answer.format(chance=html.bold(chance)) + UPDATE_AGAIN.value,
        reply_markup=k.chance(chance)
    )
    await query.answer()


@router.callback_query()
@flags.data('chance')
async def chance_handler(
        query: types.CallbackQuery,
        chance: float,
):
    await query.message.edit_text(
        _("Current text generation chance: {chance}%.").format(chance=html.bold(chance)) + UPDATE.value,
        reply_markup=k.chance(chance)
    )
    await query.answer()
