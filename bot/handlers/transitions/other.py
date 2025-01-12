import asyncio

from aiogram import F, Router, flags, types
from aiogram.utils import formatting
from aiogram.utils.i18n import gettext as _

from core import filters
from handlers.commands.settings.record.misc.helpers import clear_data
from utils import database
from utils.database.types import Int64

router = Router(name="transitions:other")


@router.my_chat_member(filters.ChatMemberUpdatedFilter(filters.LEAVE_TRANSITION))
@flags.database(("gen_settings", "gpt_settings"))
async def my_leave_handler(
    _: types.Message,
    main_settings: database.MainSettings,
    gen_settings: database.GenSettings,
    gpt_settings: database.GPTSettings,
) -> None:
    await clear_data(main_settings, gen_settings, gpt_settings)


@router.message(F.new_chat_members | F.left_chat_member)
async def join_leave_message_handler(_: types.Message) -> None:
    pass  # skip all same events


@router.message(F.migrate_to_chat_id)
async def my_migrated_from_message_handler(message: types.Message, main_settings: database.MainSettings) -> None:
    """In old chat after migration"""

    assert message.migrate_to_chat_id is not None, "wrong chat id"

    main_settings.chat_id = Int64(message.migrate_to_chat_id)
    await main_settings.save()


@router.message(F.migrate_from_chat_id)
async def my_migrated_to_message_handler(message: types.Message) -> None:
    """In new chat after migration"""

    await asyncio.sleep(1)

    content = formatting.Text(_("Ouch, it's just a migrated group..."))
    await message.answer(**content.as_kwargs())
