from aiogram import Router, Bot, F, types, flags
from aiogram.utils.i18n import gettext as _

from bot.utils.database.context import DataBaseContext
from . import UPDATE, UPDATE_AGAIN, keyboards as k

router = Router(name="settings:chance")
router.callback_query.filter(k.Settings.filter(F.name == 'chance'))


@router.callback_query(k.Settings.filter(F.value))
async def chance_update_handler(
        query: types.CallbackQuery,
        callback_data: k.Settings,
        bot: Bot,
        db: DataBaseContext
):
    chance = float(callback_data.value)

    if chance <= 10:
        answer = _("The chance of text generation has reached the limit: <b>{chance}%</b>, below is impossible.")
    elif chance >= 90:
        answer = _("The chance of text generation has reached the limit: <b>{chance}%</b>, higher is impossible.")
    else:
        answer = _("Text generation chance successfully updated: <b>{chance}%</b>.")

    answer = answer.format(chance=chance) + str(UPDATE_AGAIN)

    await db.set_data(chance=chance * await bot.get_chat_member_count(query.message.chat.id) / 100)
    await query.message.edit_text(answer, reply_markup=k.chance(chance))


@router.callback_query()
@flags.data('chance')
async def chance_handler(
        query: types.CallbackQuery,
        chance: float
):
    await query.message.edit_text(
        _("Current text generation chance: <b>{chance}%</b>.").format(chance=chance) + str(UPDATE),
        reply_markup=k.chance(chance)
    )
