import logging

from aiogram import Dispatcher


async def setup(dp: Dispatcher, database_url: str):
    logging.debug('Setting up utils...')

    from . import database, wiki
    dp['db'] = sql = await database.SQLContext.setup(database_url)

    dp.shutdown.register(sql.close)
    dp.shutdown.register(wiki.close)
