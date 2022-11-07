from aiogram import Router, filters, F, types
from aiogram.utils.i18n import gettext as _

from bot.utils.database.context import DataBaseContext

router = Router(name='transitions')


@router.message(F.migrate_to_chat_id)
async def my_migrated_from_message_handler(message: types.Message, db: DataBaseContext):
    await db.update_data(id=message.migrate_to_chat_id)


@router.message(F.migrate_from_chat_id)
async def my_migrated_to_message_handler(message: types.Message):
    await message.answer(_("Ouch, it's just a migrated group..."))


@router.message(filters.MagicData(F.event.left_chat_member.id == F.bot.id))
async def my_leave_message_handler(_):
    pass


@router.my_chat_member(filters.ChatMemberUpdatedFilter(filters.LEAVE_TRANSITION))
async def my_leave_action_handler(_, db: DataBaseContext):
    await db.clear()


def setup():
    from .group import router as chat_rt
    from .other import router as other_rt
    from .private import router as private_rt

    routers = (
        private_rt,
        chat_rt,
        other_rt,
    )

    for included_router in routers:
        router.include_router(included_router)

    return router
