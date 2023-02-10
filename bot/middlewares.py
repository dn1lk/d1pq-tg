import asyncio
from random import random, choice
from typing import Awaitable, Callable, Any

from aiogram import Dispatcher, BaseMiddleware, types
from aiogram.dispatcher.flags import get_flag
from aiogram.fsm.storage.base import StorageKey
from aiogram.utils.i18n import I18n, gettext as _


class ThrottlingMiddleware(BaseMiddleware):
    __tasks: set[asyncio.Task] = set()
    __timeouts = {
        'gen': 3,
    }

    def __init__(self, i18n: I18n):
        self.i18n = i18n

    def __setitem__(self, key: StorageKey, task: asyncio.Task):
        self.__tasks.add(task)
        task.set_name(key)
        task.add_done_callback(self.__tasks.discard)

    async def __call__(
        self,
        handler: Callable[[types.TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: types.TelegramObject,
        data: dict[str, Any],
    ):
        throttling = get_flag(data, 'throttling')

        if throttling:
            key = self.get_key(data, throttling)

            if any(task.get_name() == key for task in self.__tasks):
                if isinstance(event, types.Message | types.CallbackQuery) and random() < 0.1:
                    await self.answer(event, data)
                return

            self[key] = asyncio.create_task(asyncio.sleep(self.__timeouts[throttling]))
        return await handler(event, data)

    @staticmethod
    def get_key(data: dict[str, Any], throttling: str) -> StorageKey:
        chat_id: int = data.get('event_chat', data['event_from_user']).id
        bot_id: int = data['bot'].id

        return StorageKey(
            user_id=chat_id,
            chat_id=chat_id,
            bot_id=bot_id,
            destiny=throttling,
        )

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


def setup(dp: Dispatcher, i18n: I18n):
    from handlers.settings.commands import CustomCommandsMiddleware
    from utils.database.middleware import SQLUpdateMiddleware

    outer_middlewares = (
        (ThrottlingMiddleware(i18n=i18n), dp.message, dp.callback_query),
        (CustomCommandsMiddleware(), dp.message, dp.callback_query),
        (SQLUpdateMiddleware(), dp.message),
    )

    for middleware, *observers in outer_middlewares:
        for observer in observers:
            observer.outer_middleware(middleware)

    from aiogram.utils.chat_action import ChatActionMiddleware
    from locales.middleware import I18nContextMiddleware
    from utils.database.middleware import SQLGetMiddleware
    from utils.timer.middleware import TimerMiddleware

    inner_middlewares = (
        (I18nContextMiddleware(i18n=i18n), dp.update),
        (ChatActionMiddleware(), dp.message),
        (SQLGetMiddleware(), dp.message, dp.callback_query, dp.inline_query),
        (TimerMiddleware(), dp.message, dp.callback_query, dp.chat_member),
    )

    for middleware, *observers in inner_middlewares:
        for observer in observers:
            observer.middleware(middleware)
