import logging

from aiogram import Dispatcher

from .database import SQLContext
from .timer import TimerTasks


async def setup(dp: Dispatcher, database_url: str):
    logging.debug('Setting up utils...')

    dp['db'] = sql = await SQLContext.setup(database_url)

    from . import wiki

    dp.shutdown.register(sql.close)
    dp.shutdown.register(wiki.close)
