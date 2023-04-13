import logging

from aiogram import Router
from aiogram.utils.chat_action import ChatActionMiddleware
from aiogram.utils.i18n import I18n

from bot.core.locales.middleware import I18nContextMiddleware
from bot.core.utils.database.middleware import SQLGetMiddleware
from bot.core.utils.timer.middleware import TimerMiddleware
from .throttling import ThrottlingMiddleware


def setup(router: Router, i18n: I18n):
    logging.debug('Setting up middlewares...')

    ThrottlingMiddleware(i18n=i18n).setup(router)
    router.message.middleware(ChatActionMiddleware())

    I18nContextMiddleware(i18n=i18n).setup(router)
    SQLGetMiddleware().setup(router)
    TimerMiddleware().setup(router)
