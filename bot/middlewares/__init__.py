import logging

from aiogram import Router
from aiogram.utils.i18n import I18n


def setup(router: Router, i18n: I18n):
    logging.debug('Setting up middlewares...')

    from aiogram.utils.chat_action import ChatActionMiddleware

    from .throttling import ThrottlingMiddleware
    from bot.locales.middleware import I18nContextMiddleware
    from bot.utils.database.middleware import SQLGetMiddleware
    from bot.utils.timer.middleware import TimerMiddleware

    ThrottlingMiddleware(i18n=i18n).setup(router)
    router.message.middleware(ChatActionMiddleware())

    I18nContextMiddleware(i18n=i18n).setup(router)
    SQLGetMiddleware().setup(router)
    TimerMiddleware().setup(router)
