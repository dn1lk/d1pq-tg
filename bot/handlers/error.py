import asyncio
import logging
import traceback

from aiogram import Bot, Router, html
from aiogram.exceptions import TelegramRetryAfter, TelegramBadRequest
from aiogram.types.error_event import ErrorEvent

from core import filters

logger = logging.getLogger('bot')
router = Router(name='error')


@router.errors(filters.ExceptionTypeFilter(TelegramRetryAfter))
async def retry_after_handler(_, exception: TelegramRetryAfter):
    logger.error(exception.message)

    await asyncio.sleep(exception.retry_after)
    await exception.method


@router.errors()
async def errors_handler(event: ErrorEvent, bot: Bot, owner_id: int):
    title = f'While event {event.update.event_type}:'
    tb = traceback.format_exc(limit=-10)

    try:
        await bot.send_message(
            owner_id,
            f"{html.bold(title)}\n\n{html.pre_language(html.quote(tb), language='python')}",
        )
    except TelegramBadRequest as error:
        logger.critical(error.message)
    finally:
        logger.error(tb)
