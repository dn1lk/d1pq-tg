import logging

from aiogram import Bot, Dispatcher, types

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

        await bot.send_message(bot.owner_id, 'Bot started.')

        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        await bot.send_message(bot.owner_id, 'Bot stopped.')

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
