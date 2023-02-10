import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.webhook.aiohttp_server import SimpleRequestHandler
from aiohttp import web


async def setup(dp: Dispatcher, bot: Bot, domain_url: str, host: str, port: int):
    user = await bot.me()

    webhook_logger = logging.getLogger("aiogram.webhook")
    webhook_logger.info("Setup webhook for bot @%s id=%d - %r", user.username, bot.id, user.full_name)

    path = f'/webhook/{bot.token}'
    await bot.set_webhook(url=f'{domain_url}{path}', allowed_updates=dp.resolve_used_update_types())

    aiohttp_logger = logging.getLogger("aiohttp.access")
    aiohttp_logger.setLevel(logging.CRITICAL)

    app = web.Application()
    SimpleRequestHandler(dispatcher=dp, bot=bot).register(app, path=path)

    runner = web.AppRunner(app)
    await runner.setup()

    site = web.TCPSite(runner, host=host, port=port)
    await site.start()

    await asyncio.Event().wait()
