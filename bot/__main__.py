import logging

from aiogram import Bot

import misc

logger = logging.getLogger('bot')


@misc.dp.startup()
async def on_startup(bot: Bot, owner_id: int):
    await bot.send_message(owner_id, 'Bot starting...')


@misc.dp.shutdown()
async def on_shutdown(bot: Bot, owner_id: int):
    await bot.send_message(owner_id, 'Bot stopping...')


async def main():
    logger.info("Start bot")

    await utils.setup(misc.dp)
    # await ui_info.setup(misc.bot, misc.i18n)

    middlewares.setup(misc.dp, misc.i18n)
    handlers.setup(misc.dp)

    if config.WEBHOOK_USE:
        await webhook.start(misc.dp, misc.bot)
    else:
        await misc.dp.start_polling(misc.bot, allowed_updates=misc.dp.resolve_used_update_types())


if __name__ == "__main__":
    import asyncio

    import config

    import handlers
    import webhook
    import logs
    from core import types, utils, middlewares  # , ui_info

    logs.setup()
    types.setup()

    try:
        asyncio.run(main())
    finally:
        logger.info("Bot stopped")
