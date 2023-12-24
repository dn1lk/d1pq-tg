from aiogram import Router, F, types, html, flags
from aiogram.utils.i18n import gettext as _

from core.utils import database
from . import RecordActions, keyboards

router = Router(name="record:update")


async def update(query: types.CallbackQuery, callback_data: keyboards.RecordData):
    answer = _("{field} recording is {status}.")
    if callback_data.to_blocked:
        status_text = _("disabled")
    else:
        status_text = _("enabled")

    await query.message.edit_text(
        answer.format(field=callback_data.action.keyboard, status=html.bold(status_text))
    )

    await query.answer()


@router.callback_query(keyboards.RecordData.filter(F.action == RecordActions.MESSAGES))
@flags.database('gen_settings')
async def messages_handler(
        query: types.CallbackQuery,
        gen_settings: database.GenSettings,
        callback_data: keyboards.RecordData
):
    if callback_data.to_blocked:
        gen_settings.messages = None
    else:
        gen_settings.messages = []

    await gen_settings.save()
    await update(query, callback_data)


@router.callback_query(keyboards.RecordData.filter(F.action == RecordActions.STICKERS))
@flags.database('gen_settings')
async def messages_handler(
        query: types.CallbackQuery,
        gen_settings: database.GenSettings,
        callback_data: keyboards.RecordData
):
    if callback_data.to_blocked:
        gen_settings.stickers = None
    else:
        gen_settings.stickers = []

    await gen_settings.save()
    await update(query, callback_data)


@router.callback_query(keyboards.RecordData.filter(F.action == RecordActions.MEMBERS))
async def members_handler(
        query: types.CallbackQuery,
        main_settings: database.MainSettings,
        callback_data: keyboards.RecordData
):
    if callback_data.to_blocked:
        main_settings.members = None
    else:
        main_settings.members = [query.from_user.id]

    await main_settings.save()
    await update(query, callback_data)


@router.callback_query(keyboards.RecordData.filter(F.action == RecordActions.DELETE))
@flags.database(('gen_settings', 'gpt_settings'))
async def delete_handler(
        query: types.CallbackQuery,
        main_settings: database.MainSettings,
        gen_settings: database.GenSettings,
        gpt_settings: database.GPTSettings,
):
    await main_settings.delete()
    await gen_settings.delete()
    await gpt_settings.delete()

    await query.message.edit_text(html.bold(_("Records was successfully deleted.")))
    await query.answer()
