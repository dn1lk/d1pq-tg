import asyncio
import logging

from aiogram import Bot, Dispatcher, exceptions
from aiogram.fsm.storage.redis import RedisStorage, DefaultKeyBuilder
from aiogram.fsm.strategy import FSMStrategy

logging.basicConfig(
    level=logging.DEBUG,
    format="%(levelname)s - %(name)s - %(message)s")
logging.info("Start bot")


async def main():
    import config

    bot = Bot(token=config.bot.token.get_secret_value(), parse_mode="HTML")
    dp = Dispatcher(
        name='dispatcher',
        storage=RedisStorage.from_url(
            config.heroku.redis_url,
            key_builder=DefaultKeyBuilder(with_destiny=True),
            data_ttl=86400,  # 24 hours
        ),
        fsm_strategy=FSMStrategy.CHAT
    )

    dp['owner_id'] = config.bot.owner

    import utils

    await utils.setup(dp)

    import middlewares
    import handlers

    middlewares.setup(dp)
    handlers.setup(dp)

    try:
        from ui_commands import set_bot_commands
        dp['commands'] = await set_bot_commands(bot, dp)

        await bot.send_message(dp['owner_id'], 'Bot starting...')

        if config.heroku.domain_url:
            import webhook
            await webhook.setup(dp, bot)
        else:
            await bot.delete_webhook()
            await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        try:
            await bot.send_message(dp['owner_id'], 'Bot stopping...')
        except exceptions.TelegramNetworkError:
            logging.exception(exceptions.TelegramNetworkError)
        finally:
            await bot.session.close()
            await dp['yalm'].close()
            await dp['pool_db'].close()


if __name__ == "__main__":
    import send_message

    send_message.setup()

    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.error("Bot stopped")
