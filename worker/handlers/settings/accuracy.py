from typing import Optional

from aiogram import Router, Bot, F, types, flags
from aiogram.dispatcher.fsm.context import FSMContext
from aiogram.utils.i18n import gettext as _

from worker import keyboards as k
from worker.handlers.settings import UPDATE, UPDATE_AGAIN

router = Router(name="settings_accuracy")
router.callback_query.filter(k.SettingsData.filter(F.name == 'accuracy'))


@router.callback_query(k.SettingsData.filter(F.value))
async def settings_accuracy_two_handler(
        query: types.CallbackQuery,
        bot: Bot,
        callback_data: k.SettingsData,
        state: Optional[FSMContext] = None
):
    accuracy = int(callback_data.value)

    await bot.sql.set_data(query.message.chat.id, 'accuracy', accuracy, state)
    await query.message.edit_text(
        text=_("Text generation accuracy updated successfully: <b>{markov_state}</b>.").format(
            markov_state=accuracy
        ) + str(UPDATE_AGAIN),
        reply_markup=k.accuracy(accuracy)
    )


@router.callback_query()
@flags.data('accuracy')
async def settings_accuracy_one_handler(
        query: types.CallbackQuery,
        accuracy: int,
):
    await query.message.edit_text(
        text=_(
            "Current text generation accuracy: <b>{accuracy}</b>.\n\n"
            "The larger the value, the more accurate, but the text generation will take longer."
        ).format(accuracy=accuracy) + str(UPDATE),
        reply_markup=k.accuracy(accuracy)
    )
