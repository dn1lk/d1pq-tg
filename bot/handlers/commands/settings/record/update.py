from aiogram import Router, F, types, html
from aiogram.utils.i18n import gettext as _

from bot.core.utils import database
from bot.handlers.commands.settings.record.misc.actions import RecordActions
from .. import keyboards

router = Router(name="record:update")


async def update(query: types.CallbackQuery, callback_data: keyboards.SettingsData):
    answer = _("{data} recording is {status}.")
    await query.message.edit_text(
        answer.format(
            data=callback_data.action.keyboard,
            status=html.bold(_("disabled") if callback_data.value else _("enabled"))
        )
    )

    await query.answer()


@router.callback_query(keyboards.SettingsData.filter(F.action == RecordActions.MESSAGES))
async def messages_handler(query: types.CallbackQuery, db: database.SQLContext, callback_data: keyboards.SettingsData):
    await db.messages.set(query.message.chat.id, ["disabled"] if callback_data.value else None)
    await update(query, callback_data)


@router.callback_query(keyboards.SettingsData.filter(F.action == RecordActions.MEMBERS))
async def members_handler(query: types.CallbackQuery, db: database.SQLContext, callback_data: keyboards.SettingsData):
    await db.members.set(query.message.chat.id, None if callback_data.value else [query.from_user.id])
    await update(query, callback_data)


@router.callback_query(keyboards.SettingsData.filter(F.action == RecordActions.DELETE))
async def delete_handler(query: types.CallbackQuery, db: database.SQLContext):
    await db.clear(query.message.chat.id)

    await query.message.edit_text(html.bold(_("Records was successfully deleted.")))
    await query.answer()
