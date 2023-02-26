import asyncio
import logging
from random import random, choice
from typing import Awaitable, Callable, Any, Coroutine

from aiogram import Router, BaseMiddleware, types
from aiogram.dispatcher.flags import get_flag
from aiogram.fsm.storage.base import StorageKey
from aiogram.utils.i18n import I18n, gettext as _


def get_key(data: dict[str, Any], destiny: str) -> StorageKey:
    chat_id: int = data.get('event_chat', data['event_from_user']).id
    bot_id: int = data['bot'].id

    return StorageKey(
        user_id=chat_id,
        chat_id=chat_id,
        bot_id=bot_id,
        destiny=destiny,
    )


class ThrottlingMiddleware(BaseMiddleware):
    __tasks: set[asyncio.Task] = set()
    __timeouts = {
        'gen': 3,
        'rps': 3,
    }

    def __init__(self, i18n: I18n):
        self.i18n = i18n

    def __setitem__(self, key: StorageKey, coro: Coroutine):
        task = asyncio.create_task(coro)

        self.__tasks.add(task)
        task.set_name(key)
        task.add_done_callback(self.__tasks.discard)

    def __getitem__(self, key: StorageKey):
        for task in self.__tasks:
            if task.get_name() == str(key):
                yield task

    async def __call__(
            self,
            handler: Callable[[types.TelegramObject, dict[str, Any]], Awaitable[Any]],
            event: types.TelegramObject,
            data: dict[str, Any],
    ):
        throttling = get_flag(data, 'throttling')

        if throttling:
            key = get_key(data, throttling)

            if any(self[key]):
                if isinstance(event, types.Message | types.CallbackQuery) and random() < 0.3:
                    await self.answer(event, data)
                return

            self[key] = asyncio.sleep(self.__timeouts[throttling])
        return await handler(event, data)

    async def answer(self, event: types.Message | types.CallbackQuery, data: dict):
        from locales.middleware import I18nContextMiddleware
        locale = await I18nContextMiddleware(self.i18n).get_locale(event, data)

        with self.i18n.context(), self.i18n.use_locale(locale):
            answer = choice(
                (
                    _("Stop spamming!"),
                    _("How much information..."),
                    _("Ahhh...")
                )
            )

            await event.answer(answer)

    def setup(self, router: Router):
        for observer in router.message, router.callback_query:
            observer.middleware(self)


def setup(router: Router, i18n: I18n):
    logging.debug('Setting up middlewares...')

    ThrottlingMiddleware(i18n=i18n).setup(router)

    from aiogram.utils.chat_action import ChatActionMiddleware
    from locales.middleware import I18nContextMiddleware
    from utils.database.middleware import SQLGetMiddleware
    from utils.timer.middleware import TimerMiddleware

    router.message.middleware(ChatActionMiddleware())

    I18nContextMiddleware(i18n=i18n).setup(router)
    SQLGetMiddleware().setup(router)
    TimerMiddleware().setup(router)
