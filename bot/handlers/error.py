import asyncio
import logging
import traceback

from aiogram import Bot, Router, html
from aiogram.exceptions import TelegramRetryAfter, TelegramBadRequest
from aiogram.types.error_event import ErrorEvent

from bot.core import filters

router = Router(name='error')


@router.errors(filters.ExceptionTypeFilter(TelegramRetryAfter))
async def retry_after_handler(_, exception: TelegramRetryAfter):
    logging.error(exception.message)

    await asyncio.sleep(exception.retry_after)
    await exception.method


@router.errors()
async def errors_handler(event: ErrorEvent, bot: Bot, owner_id: int):
    title = f'While event {event.update.event_type}:'
    tracback = '\n'.join(traceback.format_exc(limit=10).splitlines())

    try:
        await bot.send_message(
            owner_id,
            f"{html.bold(title)}\n\n{html.pre_language(html.quote(tracback), language='python')}",
        )
    except TelegramBadRequest:
        logging.critical("TelegramBadRequest: can't send error message")
    finally:
        logging.error(title + tracback)
