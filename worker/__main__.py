import logging

from aiogram import Bot, Dispatcher, types
from aiogram.dispatcher.webhook.aiohttp_server import SimpleRequestHandler
from aiohttp import web

import config
import handlers
import middlewares
from ui_commands import set_bot_commands
from utils import postgresql as sql

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s - %(name)s - %(message)s")
logging.info("Start bot")


async def main():
    bot: Bot = Bot(token=config.bot.token.get_secret_value(), parse_mode="HTML")

    dp: Dispatcher = handlers.setup()
    dp: Dispatcher = middlewares.setup(dp)

    try:
        bot.owner_id = int(config.bot.owner)
        bot.commands = await set_bot_commands(bot, dp, config.i18n.available_locales)

        bot.sql = await sql.setup()

        await bot.set_webhook(
            url=config.webhook + '/webhook/' + bot.token,
            allowed_updates=dp.resolve_used_update_types()
        )

        app = web.Application()
        SimpleRequestHandler(dispatcher=dp, bot=bot).register(app, path='/webhook/' + bot.token)
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, host='0.0.0.0', port=int(config.port))
        await site.start()

        await bot.send_message(bot.owner_id, 'Bot started.')

        await asyncio.Event().wait()
    finally:
        await bot.send_message(bot.owner_id, 'Bot stopped.')

        await bot.delete_webhook()

        await dp.storage.close()
        await bot.sql.pool.close()
        await bot.session.close()


if __name__ == "__main__":
    from send_message import AddMessage

    types.Message.answer = AddMessage.answer
    types.Message.reply = AddMessage.reply

    types.Message.answer_sticker = AddMessage.answer_sticker
    types.Message.answer_voice = AddMessage.answer_voice

    try:
        import asyncio

        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.error("Bot stopped")
