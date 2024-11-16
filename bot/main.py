from aiogram import Bot, Dispatcher, enums
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.base import DefaultKeyBuilder
from aiogram.fsm.storage.redis import RedisStorage
from aiogram.fsm.strategy import FSMStrategy
from aiogram.utils import formatting
from aiogram.utils.i18n import I18n

import config

bot = Bot(
    token=config.BOT_TOKEN,
    default=DefaultBotProperties(
        parse_mode=enums.ParseMode.MARKDOWN_V2,
    ),
)

i18n = I18n(path=config.LOCALE_PATH, domain="messages")

if config.REDIS_USE:
    storage = RedisStorage.from_url(
        config.REDIS_URL,
        key_builder=DefaultKeyBuilder(with_destiny=True),
        data_ttl=60 * 60 * 24,  # one day
    )
else:
    storage = None

dp = Dispatcher(
    name="dispatcher",
    storage=storage,
    fsm_strategy=FSMStrategy.CHAT,
    owner_id=config.BOT_OWNER_ID,
)


@dp.startup()
async def on_startup(bot: Bot, owner_id: int) -> None:
    content = formatting.Text("bot starting...")
    await bot.send_message(owner_id, disable_notification=True, **content.as_kwargs())


@dp.shutdown()
async def on_shutdown(bot: Bot, owner_id: int) -> None:
    content = formatting.Text("bot stopping...")
    await bot.send_message(owner_id, disable_notification=True, **content.as_kwargs())


def main() -> None:
    utils.setup(dp)
    middlewares.setup(bot, dp, i18n)
    handlers.setup(dp)

    # ui_info.setup(dp)

    if config.WEBHOOK_USE:
        webhook.start(dp, bot)
    else:
        dp.run_polling(bot, allowed_updates=dp.resolve_used_update_types())


if __name__ == "__main__":
    import logging

    import handlers
    import logs
    import utils
    import webhook
    from core import middlewares, types, ui_info

    logs.setup()
    types.setup()
    logger = logging.getLogger("bot")

    try:
        logger.info("starting bot...")
        main()
    finally:
        logger.info("bot stopped")
