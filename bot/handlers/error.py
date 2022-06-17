import logging

from aiogram import Router, Bot, types, exceptions

router = Router(name='error')


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
        logging.critical("TelegramBadRequest: Can't send error message")
    finally:
        logging.exception(exception)
