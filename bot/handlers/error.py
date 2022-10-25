import asyncio
import logging
import traceback

from aiogram import Router, Bot, filters, exceptions
from aiogram.types.error_event import ErrorEvent

router = Router(name='error')


@router.errors(filters.ExceptionTypeFilter(exceptions.TelegramRetryAfter))
async def retry_after_handler(_, exception: exceptions.TelegramRetryAfter):
    logging.error(exception)

    await asyncio.sleep(exception.retry_after)
    await exception.method


@router.errors(filters.ExceptionTypeFilter(exceptions.TelegramBadRequest))
async def edit_handler(event: ErrorEvent, bot: Bot):
    if event.update.callback_query:
        await event.update.callback_query.answer("↻ - please wait...")
    else:
        await errors_handler(event, bot)


@router.errors()
async def errors_handler(event: ErrorEvent, bot: Bot):
    trcback = traceback.format_exc().splitlines()
    formatted_trcback = "/n".join(trcback[:-3])
    
    try:
        await bot.send_message(
            bot.owner_id,
            (
                f'ERROR while event <b>{event.update.event_type}</b>\n\n'
                f'{formatted_trcback}'
            )
        )
    except exceptions.TelegramBadRequest:
        logging.critical("TelegramBadRequest: can't send error message")
    finally:
        logging.error(formatted_trcback)
