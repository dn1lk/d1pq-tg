import asyncio
import logging
import traceback

from aiogram import Bot, Router, types, exceptions, html, flags
from aiogram.types.error_event import ErrorEvent

from core import filters
from core.utils import database

logger = logging.getLogger('bot')
router = Router(name='error')


@router.errors(filters.ExceptionTypeFilter(exceptions.TelegramRetryAfter))
async def retry_after_handler(_, exception: exceptions.TelegramRetryAfter):
    logger.error(exception.message)

    await asyncio.sleep(exception.retry_after)
    await exception.method


@router.errors(filters.ExceptionTypeFilter(exceptions.TelegramForbiddenError))
@flags.database('gen_settings')
async def forbidden_handler(
        event: ErrorEvent,
        main_settings: database.MainSettings,
        gen_settings: database.GenSettings,
        event_chat: types.Chat = None,
):
    logger.error(event.exception)

    if event_chat:
        assert event_chat.id == main_settings.chat_id == gen_settings.chat_id

        await main_settings.delete()
        await gen_settings.delete()
        logger.info(f"Data chat id={event_chat.id} was deleted")


@router.errors()
async def errors_handler(event: ErrorEvent, bot: Bot, owner_id: int):
    title = f'While event {event.update.event_type}:'
    tb = traceback.format_exc(limit=-10)

    try:
        await bot.send_message(
            owner_id,
            f"{html.bold(title)}\n\n{html.pre_language(html.quote(tb), language='python')}",
        )
    except exceptions.TelegramBadRequest as exception:
        logger.critical(exception.message)
    finally:
        logger.error(tb)
