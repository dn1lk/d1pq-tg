import asyncio
import logging

from aiogram import Dispatcher, Bot
from aiogram.dispatcher.webhook.aiohttp_server import SimpleRequestHandler
from aiohttp import web

import config


async def start(dp: Dispatcher, bot: Bot):
    await bot.set_webhook(
        url=config.heroku.domain_url + '/webhook/' + bot.token,
        allowed_updates=dp.resolve_used_update_types()
    )

    aiohttp_logger = logging.getLogger("aiohttp.access")
    aiohttp_logger.setLevel(logging.CRITICAL)

    app = web.Application()
    SimpleRequestHandler(dispatcher=dp, bot=bot).register(app, path='/webhook/' + bot.token)

    runner = web.AppRunner(app)
    await runner.setup()

    site = web.TCPSite(runner, host=config.heroku.host, port=int(config.heroku.port))
    await site.start()

    await asyncio.Event().wait()
