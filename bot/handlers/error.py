import asyncio
import logging

from aiogram import Router, Bot, types, exceptions

router = Router(name='error')


@router.errors(
    pattern=(
                    "Bad Request: message is not modified: "
                    "specified new message content and reply markup are exactly "
                    "the same as a current content and reply markup of the message"
    )
)
async def edit_handler(_):
    pass


@router.errors(exception=exceptions.TelegramRetryAfter)
async def retry_after_handler(_, exception: exceptions.TelegramRetryAfter):
    logging.error(f'TelegramRetryAfter: sleeping for {exception.retry_after} seconds')

    await asyncio.sleep(exception.retry_after)
    await exception.method


@router.errors()
async def errors_handler(event: types.Update, bot: Bot, exception: Exception):
    try:
        await bot.send_message(
            bot.owner_id,
            (
                f'ERROR while event <b>{event.event_type}</b>:\n\n'
                f'- <b>exception</b>: {exception}.'
            )
        )
    except exceptions.TelegramBadRequest:
        logging.critical("TelegramBadRequest: can't send error message")
    finally:
        logging.exception(exception)
