import asyncio
import logging

from aiogram import Bot, Dispatcher
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
        fsm_strategy=FSMStrategy.CHAT
    )

    dp['owner_id'] = owner_id = config.bot.owner

    import utils

    await utils.setup(dp, config.provider.database_url)

    import middlewares
    import handlers

    middlewares.setup(dp, config.i18n)
    handlers.setup(dp)

    try:
        import ui_commands
        dp['ui_commands'] = await ui_commands.setup(bot, config.i18n)

        await bot.send_message(owner_id, 'Bot starting...')

        if config.provider.domain_url:
            import webhook
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
    from bot import types
    types.setup()

    try:
        asyncio.run(main())
    finally:
        logging.error("Bot stopped")
