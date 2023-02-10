from aiogram import Router, F, types, html
from aiogram.fsm.context import FSMContext
from aiogram.utils.i18n import gettext as _

from .misc.data import RecordData
from ..misc import keyboards as k
from ....utils import database

router = Router(name="settings:record:process")


async def update(query: types.CallbackQuery, callback_data: k.SettingsKeyboard):
    answer = _("{data} recording is {status}.")
    await query.message.edit_text(
        answer.format(
            data=callback_data.action.word,
            status=html.bold(_("disabled") if callback_data.value else _("enabled"))
        )
    )

    await query.answer()


@router.callback_query(k.SettingsKeyboard.filter(F.action == RecordData.MESSAGES))
async def messages_handler(query: types.CallbackQuery, db: database.SQLContext, callback_data: k.SettingsKeyboard):
    await db.set_data(messages=["disabled"] if callback_data.value else None)
    await update(query, callback_data)


@router.callback_query(k.SettingsKeyboard.filter(F.action == RecordData.MEMBERS))
async def members_handler(query: types.CallbackQuery, db: database.SQLContext, callback_data: k.SettingsKeyboard):
    await db.set_data(members=None if callback_data.value else [query.from_user.id])
    await update(query, callback_data)


@router.callback_query(k.SettingsKeyboard.filter(F.action == RecordData.DELETE))
async def delete_handler(query: types.CallbackQuery, state: FSMContext, db: database.SQLContext):
    await db.clear(query.message.chat.id)
    await state.clear()

    await query.message.edit_text(html.bold(_("Records was successfully deleted.")))
    await query.answer()
