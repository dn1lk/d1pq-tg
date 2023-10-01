import asyncio

from aiogram import Router, F, types, flags
from aiogram.utils.i18n import gettext as _

from core import filters
from core.utils import database

router = Router(name='transitions:other')


@router.my_chat_member(filters.ChatMemberUpdatedFilter(filters.LEAVE_TRANSITION))
@flags.database('gen_settings')
async def my_leave_handler(_, main_settings: database.MainSettings, gen_settings: database.GenSettings):
    await main_settings.delete()
    await gen_settings.delete()


@router.message(F.new_chat_members | F.left_chat_member)
async def join_leave_message_handler(_):
    pass  # skip all same events


@router.message(F.migrate_to_chat_id)
async def my_migrated_from_message_handler(message: types.Message, main_settings: database.MainSettings):
    """In old chat after migration"""

    main_settings.chat_id = message.migrate_to_chat_id
    await main_settings.save()


@router.message(F.migrate_from_chat_id)
async def my_migrated_to_message_handler(message: types.Message):
    """In new chat after migration"""

    await asyncio.sleep(1)
    await message.answer(_("Ouch, it's just a migrated group..."))
