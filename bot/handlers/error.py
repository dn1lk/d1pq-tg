import traceback

from aiogram import Bot, Router, exceptions, flags, loggers, types
from aiogram.types.error_event import ErrorEvent
from aiogram.utils import formatting

from core import filters
from handlers.commands.settings.record.misc.helpers import clear_data
from utils import database

router = Router(name="error")


@router.errors(filters.ExceptionTypeFilter(exceptions.TelegramForbiddenError))
@flags.database("gen_settings")
async def forbidden_handler(
    event: ErrorEvent,
    main_settings: database.MainSettings,
    gen_settings: database.GenSettings,
    gpt_settings: database.GPTSettings,
    event_chat: types.Chat | None = None,
) -> None:
    loggers.event.error(event.exception)

    if event_chat:
        assert event_chat.id == main_settings.chat_id == gen_settings.chat_id

        await clear_data(main_settings, gen_settings, gpt_settings)

        loggers.event.info("data chat id=%i was deleted", event_chat.id)


@router.errors()
async def errors_handler(event: ErrorEvent, bot: Bot, owner_id: int) -> None:
    _title = f"While event {event.update.event_type}:"
    _tb = traceback.format_exc(limit=-10)
    content = formatting.Text(
        formatting.Bold(_title),
        "\n\n",
        formatting.Pre(_tb, language="python"),
    )

    try:
        await bot.send_message(owner_id, **content.as_kwargs())
    except exceptions.TelegramBadRequest as exception:
        loggers.event.critical(exception.message)
    finally:
        loggers.event.error(_tb)
