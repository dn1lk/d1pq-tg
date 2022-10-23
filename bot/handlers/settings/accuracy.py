from aiogram import Router, F, types, flags
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

    await db.set_data(accuracy=accuracy)
    await query.message.edit_text(
        _("Text generation accuracy updated successfully: <b>{markov_state}</b>.").format(
            markov_state=accuracy
        ) + str(UPDATE_AGAIN),
        reply_markup=k.accuracy(accuracy)
    )


@router.callback_query()
@flags.data('accuracy')
async def accuracy_handler(
        query: types.CallbackQuery,
        accuracy: int,
):
    await query.message.edit_text(
        _(
            "Current text generation accuracy: <b>{accuracy}</b>.\n\n"
            "The larger the value, the more accurate, but the text generation will take longer."
        ).format(accuracy=accuracy) + str(UPDATE),
        reply_markup=k.accuracy(accuracy)
    )
