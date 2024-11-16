import logging

from aiogram import Dispatcher

from . import clients, database
from .generation import YandexGPT
from .timer import TimerTasks

logger = logging.getLogger("bot")


def setup(dp: Dispatcher) -> None:
    logger.debug("setting up utils...")

    dp["timer"] = timer = TimerTasks()
    dp["gpt"] = YandexGPT(dp.storage, timer)

    dp.startup.register(database.setup)
    dp.startup.register(clients.setup)

    dp.shutdown.register(timer.close)
