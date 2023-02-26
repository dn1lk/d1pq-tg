import asyncio

from aiogram import Router, F, types
from aiogram.utils.i18n import gettext as _

from bot import filters
from bot.utils import database

router = Router(name='transitions:other')


@router.my_chat_member(filters.ChatMemberUpdatedFilter(filters.LEAVE_TRANSITION))
async def my_leave_action_handler(event: types.ChatMemberUpdated, db: database.SQLContext):
    await db.clear(event.chat.id)


@router.message(F.new_chat_members | F.left_chat_member)
async def join_leave_message_handler(_):
    pass


@router.message(F.migrate_to_chat_id)
async def my_migrated_from_message_handler(message: types.Message, db: database.SQLContext):
    await db.id.update(message.chat.id, message.migrate_to_chat_id)


@router.message(F.migrate_from_chat_id)
async def my_migrated_to_message_handler(message: types.Message):
    await asyncio.sleep(1)
    await message.answer(_("Ouch, it's just a migrated group..."))
