import logging

from aiogram import Bot, Router
from aiogram.utils.i18n import I18n

from core.locales.middleware import I18nContextMiddleware
from core.middlewares.session import SessionRateLimiterMiddleware, SessionRetryMiddleware
from utils.database.middlewares import SQLGetFlagsMiddleware, SQLGetMainMiddleware, SQLUpdateMiddleware
from utils.timer.middleware import TimerMiddleware

from .destiny import DestinySetMiddleware
from .throttling import ThrottlingMiddleware

__all__ = (
    "DestinySetMiddleware",
    "I18nContextMiddleware",
    "SQLGetFlagsMiddleware",
    "SQLGetMainMiddleware",
    "SQLUpdateMiddleware",
    "SessionRateLimiterMiddleware",
    "SessionRetryMiddleware",
    "ThrottlingMiddleware",
    "TimerMiddleware",
)

logger = logging.getLogger("bot")


def setup(bot: Bot, router: Router, i18n: I18n):
    logger.debug("setting up middlewares...")

    SessionRateLimiterMiddleware().setup(bot)
    SessionRetryMiddleware().setup(bot)

    # Outer middlewares
    SQLGetMainMiddleware().setup(router)
    I18nContextMiddleware(i18n=i18n).setup(router)

    # Inner middlewares
    ThrottlingMiddleware(i18n=i18n).setup(router)
    TimerMiddleware().setup(router)
    SQLGetFlagsMiddleware().setup(router)
