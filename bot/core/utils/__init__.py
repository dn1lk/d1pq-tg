import logging

from aiogram import Dispatcher

from . import database
from .generation import YandexGPT
from .timer import TimerTasks

logger = logging.getLogger('bot')


async def setup(dp: Dispatcher):
    logger.debug('Setting up utils...')

    dp['timer'] = TimerTasks()
    dp['gpt'] = await YandexGPT.setup(dp.storage)

    await database.setup(dp)
