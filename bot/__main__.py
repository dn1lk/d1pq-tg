import asyncio
import logging

from aiogram import Bot, Dispatcher, exceptions
from aiogram.fsm.storage.redis import RedisStorage, DefaultKeyBuilder

logging.basicConfig(
    level=logging.DEBUG,
    format="%(levelname)s - %(name)s - %(message)s")
logging.info("Start bot")


async def main():
    from aiogram.fsm.strategy import FSMStrategy

    import config

    bot = Bot(token=config.bot.token.get_secret_value(), parse_mode="HTML")
    dp = Dispatcher(
        name='dispatcher',
        storage=RedisStorage.from_url(
            config.heroku.redis_url,
            key_builder=DefaultKeyBuilder(with_destiny=True),
            data_ttl=60 * 60 * 25 * 7,
        ),
        fsm_strategy=FSMStrategy.CHAT
    )

    from utils import database as db, balaboba as yalm

    dp['pool_db'] = pool_db = await db.setup()
    dp['yalm'] = yalm = await yalm.Yalm().setup()

    import middlewares
    import handlers

    middlewares.setup(dp)
    handlers.setup(dp)

    try:
        from ui_commands import set_bot_commands

        bot.owner_id = int(config.bot.owner)
        bot.commands = await set_bot_commands(bot, dp)

        await bot.send_message(bot.owner_id, 'Bot starting...')

        if config.heroku.domain_url:
            import webhook

            await webhook.setup(dp, bot)
        else:
            await bot.delete_webhook()
            await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        try:
            await bot.send_message(bot.owner_id, 'Bot stopping...')

        except exceptions.TelegramNetworkError:
            logging.exception(exceptions.TelegramNetworkError)

        finally:
            await bot.session.close()
            await yalm.session.close()
            await pool_db.close()


if __name__ == "__main__":
    import send_message

    send_message.setup()

    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.error("Bot stopped")
