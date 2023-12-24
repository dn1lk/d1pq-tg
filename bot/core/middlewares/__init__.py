import logging

from aiogram import Router
from aiogram.utils.chat_action import ChatActionMiddleware
from aiogram.utils.i18n import I18n

from core.locales.middleware import I18nContextMiddleware
from core.utils.database.middlewares import SQLGetMainMiddleware, SQLGetFlagsMiddleware, SQLUpdateMiddleware
from core.utils.timer.middleware import TimerMiddleware
from .destiny import DestinySetMiddleware
from .throttling import ThrottlingMiddleware

__all__ = (
    "ChatActionMiddleware",
    "I18nContextMiddleware",
    "SQLGetMainMiddleware",
    "SQLGetFlagsMiddleware",
    "SQLUpdateMiddleware",
    "TimerMiddleware",
    "ThrottlingMiddleware",
    "DestinySetMiddleware"
)

logger = logging.getLogger('bot')


def setup(router: Router, i18n: I18n):
    logger.debug('Setting up middlewares...')

    # Outer middlewares
    SQLGetMainMiddleware().setup(router)
    I18nContextMiddleware(i18n=i18n).setup(router)

    # Inner middlewares
    ThrottlingMiddleware(i18n=i18n).setup(router)
    router.message.middleware(ChatActionMiddleware())
    TimerMiddleware().setup(router)
    SQLGetFlagsMiddleware().setup(router)
