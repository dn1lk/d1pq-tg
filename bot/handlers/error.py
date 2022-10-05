import asyncio
import logging
import traceback

from aiogram import Router, Bot, types, filters, exceptions

router = Router(name='error')


@router.errors(filters.ExceptionTypeFilter(exceptions.TelegramBadRequest))
async def edit_handler(event: types.Update, bot: Bot):
    if event.callback_query:
        await event.callback_query.answer("↻ - please wait...")
    else:
        await errors_handler(event, bot)


@router.errors(filters.ExceptionTypeFilter(exceptions.TelegramRetryAfter))
async def retry_after_handler(_, exception: exceptions.TelegramRetryAfter):
    logging.error(exception)

    await asyncio.sleep(exception.retry_after)
    await exception.method


@router.errors()
async def errors_handler(event: types.Update, bot: Bot):
    try:
        await bot.send_message(
            bot.owner_id,
            (
                f'ERROR while event <b>{event.event_type}</b>\n\n'
                f'{traceback.format_exc(limit=10)}'
            )
        )
    except exceptions.TelegramBadRequest:
        logging.critical("TelegramBadRequest: can't send error message")
    finally:
        raise
