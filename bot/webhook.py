import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.webhook.aiohttp_server import SimpleRequestHandler
from aiohttp import web

import config

logger = logging.getLogger("aiogram.webhook")


async def set_webhook(dp: Dispatcher, bot: Bot):
    try:
        await bot.set_webhook(url=f'{config.WEBHOOK_URL}/{config.WEBHOOK_PATH}',
                              secret_token=config.WEBHOOK_SECRET,
                              allowed_updates=dp.resolve_used_update_types())
    finally:
        await bot.session.close()


async def start(dp: Dispatcher, bot: Bot):
    user = await bot.me()

    logger.info("Setup webhook for bot @%s id=%d - %r host=%s, port=%s",
                user.username, bot.id, user.full_name, config.WEBHOOK_HOST, config.WEBHOOK_PORT)

    aiohttp_logger = logging.getLogger("aiohttp.access")
    aiohttp_logger.setLevel(logging.CRITICAL)

    app = web.Application()
    SimpleRequestHandler(dp, bot, secret_token=config.WEBHOOK_SECRET).register(app, path=f"/{config.WEBHOOK_PATH}")

    runner = web.AppRunner(app)
    await runner.setup()

    site = web.TCPSite(runner, host=config.WEBHOOK_HOST, port=config.WEBHOOK_PORT)
    await site.start()

    # Inf looping
    await asyncio.Event().wait()


if __name__ == "__main__":
    import misc
    import handlers

    handlers.setup(misc.dp)
    asyncio.run(set_webhook(misc.dp, misc.bot))
