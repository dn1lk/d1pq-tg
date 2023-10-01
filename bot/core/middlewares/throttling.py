import asyncio
from dataclasses import replace
from random import random, choice
from typing import Callable, Any, Awaitable

from aiogram import BaseMiddleware, types, Router
from aiogram.dispatcher.flags import get_flag
from aiogram.fsm.context import FSMContext
from aiogram.utils.i18n import I18n, gettext as _

from ..utils import TimerTasks


class ThrottlingMiddleware(BaseMiddleware):
    _tags = {
        'gen': 3,
        'rps': 1,
    }

    __slots__ = {"i18n"}

    def __init__(self, i18n: I18n):
        self.i18n = i18n

    async def __call__(
            self,
            handler: Callable[[types.TelegramObject, dict[str, Any]], Awaitable[Any]],
            event: types.TelegramObject,
            data: dict[str, Any],
    ):
        throttling: str | None = get_flag(data, 'throttling')

        if throttling:
            timer: TimerTasks = data['timer']
            state: FSMContext = data['state']
            key = replace(state.key, destiny=f'throttling:{throttling}')

            if any(timer[key]):
                if isinstance(event, types.Message | types.CallbackQuery) and random() < 0.3:
                    await self.answer(event, data)
                return

            timer[key] = asyncio.sleep(self._tags[throttling])
        return await handler(event, data)

    async def answer(self, event: types.Message | types.CallbackQuery, data: dict):
        from ..locales.middleware import I18nContextMiddleware
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
