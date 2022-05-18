from typing import Optional

from aiogram import Router, Bot, F, types, flags
from aiogram.dispatcher.fsm.context import FSMContext
from aiogram.utils.i18n import gettext as _

from worker import keyboards as k
from worker.handlers.settings import UPDATE, UPDATE_AGAIN

router = Router(name="chance_settings")
router.callback_query.filter(k.SettingsData.filter(F.name == 'chance'))


@router.callback_query(k.SettingsData.filter(F.value))
async def settings_chance_two_handler(
        query: types.CallbackQuery,
        callback_data: k.SettingsData,
        bot: Bot,
        state: Optional[FSMContext] = None
):
    chance = round(float(callback_data.value), 2)

    if chance <= 10:
        answer = _(
            "The chance of text generation has reached the limit: <b>{chance}%</b>, below is impossible."
        )
    elif chance >= 90:
        answer = _(
            "The chance of text generation has reached the limit: <b>{chance}%</b>, higher is impossible."
        )
    else:
        answer = _(
            "Text generation chance successfully updated: <b>{chance}%</b>."
        )

    answer = answer.format(chance=chance) + str(UPDATE_AGAIN)

    if query.message.text != answer:
        await query.message.edit_text(text=answer, reply_markup=k.chance(chance))

        await bot.sql.set_data(
            query.message.chat.id,
            'chance',
            chance * await bot.get_chat_member_count(query.message.chat.id) / 100,
            state
        )


@router.callback_query()
@flags.data('chance')
async def settings_chance_one_handler(
        query: types.CallbackQuery,
        chance: float
):
    await query.message.edit_text(
        text=_(
            "Current text generation chance: <b>{chance}%</b>."
        ).format(chance=chance) + str(UPDATE),
        reply_markup=k.chance(chance)
    )
