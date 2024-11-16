import asyncio
import logging

from aiogram import Bot, Dispatcher, loggers
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web

import config


async def set_webhook(dp: Dispatcher, bot: Bot) -> None:
    try:
        await bot.set_webhook(
            url=f"{config.WEBHOOK_URL}/{config.WEBHOOK_PATH}",
            secret_token=config.WEBHOOK_SECRET,
            allowed_updates=dp.resolve_used_update_types(),
            drop_pending_updates=config.BOT_SKIP_UPDATES,
        )
    finally:
        await bot.session.close()


def start(dp: Dispatcher, bot: Bot) -> None:
    loggers.webhook.info(
        "Setup webhook for bot id=%d - host=%s, port=%s",
        bot.id,
        config.WEBHOOK_HOST,
        config.WEBHOOK_PORT,
    )

    aiohttp_logger = logging.getLogger("aiohttp.access")
    aiohttp_logger.setLevel(logging.CRITICAL)

    app = web.Application()
    SimpleRequestHandler(dp, bot, secret_token=config.WEBHOOK_SECRET).register(app, path=f"/{config.WEBHOOK_PATH}")

    setup_application(app, dp, bot=bot)
    web.run_app(app, host=config.WEBHOOK_HOST, port=config.WEBHOOK_PORT)


if __name__ == "__main__":
    import handlers
    from main import bot, dp

    handlers.setup(dp)
    asyncio.run(set_webhook(dp, bot))
