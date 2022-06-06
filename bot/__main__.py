import asyncio
import logging

from aiogram import Bot, Dispatcher


logging.basicConfig(
    level=logging.DEBUG,
    format="%(levelname)s - %(name)s - %(message)s")
logging.info("Start bot")


async def main():
    from aiogram.dispatcher.fsm.strategy import FSMStrategy

    import config

    bot = Bot(token=config.bot.token.get_secret_value(), parse_mode="HTML")
    dp = Dispatcher(name='dispatcher', fsm_strategy=FSMStrategy.CHAT)

    from utils import database as db

    db_pool = await db.setup()

    import middlewares
    import handlers

    middlewares.setup(dp)
    handlers.setup(dp)

    try:
        from ui_commands import set_bot_commands

        bot.owner_id = int(config.bot.owner)
        bot.commands = await set_bot_commands(bot, dp)

        if config.heroku.domain_url:
            import webhook

            await webhook.setup(dp, bot, db_pool=db_pool)
        else:
            await bot.delete_webhook()
            await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types(), db_pool=db_pool)
    finally:
        await db_pool.close()
        await bot.send_message(bot.owner_id, 'Bot stopped.')


if __name__ == "__main__":
    import send_message

    send_message.setup()

    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.error("Bot stopped")
