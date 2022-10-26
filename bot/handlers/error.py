import asyncio
import logging
import traceback

from aiogram import Router, Bot, html
from aiogram.exceptions import TelegramRetryAfter, TelegramBadRequest
from aiogram.filters import ExceptionTypeFilter, ExceptionMessageFilter
from aiogram.types.error_event import ErrorEvent

router = Router(name='error')


@router.errors(ExceptionTypeFilter(TelegramRetryAfter))
async def retry_after_handler(_, exception: TelegramRetryAfter):
    logging.error(exception)

    await asyncio.sleep(exception.retry_after)
    await exception.method


@router.errors(ExceptionMessageFilter('Bad Request: message is not modified'))
async def edit_handler(event: ErrorEvent, bot: Bot):
    if event.update.callback_query:
        await event.update.callback_query.answer("↻ - please wait...")
    else:
        await errors_handler(event, bot)


@router.errors()
async def errors_handler(event: ErrorEvent, bot: Bot, owner_id: int):
    title = f'While event {event.update.event_type}:\n\n'
    tracback = '\n'.join(traceback.format_exc().splitlines()[-9:])

    try:
        await bot.send_message(owner_id, html.bold(title) + html.pre_language(html.quote(tracback), language='python'))
    except TelegramBadRequest:
        logging.critical("TelegramBadRequest: can't send error message")
    finally:
        logging.error(title + tracback)
