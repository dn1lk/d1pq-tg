import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.redis import RedisStorage
from aiogram.fsm.strategy import FSMStrategy

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s - %(name)s - %(message)s"
)


async def main():
    logging.info("Start bot")

    import config

    bot = Bot(token=config.bot.token.get_secret_value(), parse_mode="HTML")
    dp = Dispatcher(
        name='dispatcher',
        storage=RedisStorage.from_url(config.provider.redis_url) if config.provider.redis_url else None,
        fsm_strategy=FSMStrategy.CHAT
    )

    dp['owner_id'] = owner_id = config.bot.owner

    await utils.setup(dp, config.provider.database_url)

    import handlers

    middlewares.setup(dp, config.i18n)
    handlers.setup(dp)

    try:
        await ui_commands.setup(bot, config.i18n)

        await bot.send_message(owner_id, 'Bot starting...')

        if config.provider.domain_url:
            await webhook.setup(dp, bot,
                                config.provider.domain_url, config.provider.host, config.provider.port)
        else:
            await bot.delete_webhook()
            await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        try:
            await bot.send_message(owner_id, 'Bot stopping...')
        finally:
            await bot.session.close()


if __name__ == "__main__":
    from bot.core import types, ui_commands, webhook, utils, middlewares

    types.setup()

    try:
        asyncio.run(main())
    finally:
        logging.error("Bot stopped")
