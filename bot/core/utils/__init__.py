import logging

from aiogram import Dispatcher

from . import database
from .timer import TimerTasks

logger = logging.getLogger('bot')


async def setup(dp: Dispatcher):
    logger.debug('Setting up utils...')

    dp['timer'] = TimerTasks()

    await database.setup(dp)
