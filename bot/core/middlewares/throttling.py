import asyncio
import secrets
from collections.abc import Awaitable, Callable
from dataclasses import replace
from typing import TYPE_CHECKING, Any, ClassVar

from aiogram import BaseMiddleware, Router, types
from aiogram.dispatcher.flags import get_flag
from aiogram.utils import formatting
from aiogram.utils.i18n import I18n
from aiogram.utils.i18n import gettext as _

if TYPE_CHECKING:
    from aiogram.fsm.context import FSMContext

    from utils import TimerTasks

ANSWER_CHANCE = 0.3


class ThrottlingMiddleware(BaseMiddleware):
    _tags: ClassVar[dict[str, int]] = {
        "gen": 3,
        "rps": 1,
    }

    __slots__ = {"i18n"}

    def __init__(self, i18n: I18n):
        self.i18n = i18n

    async def __call__(
        self,
        handler: Callable[[types.TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: types.TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        throttling: str | None = get_flag(data, "throttling")

        if throttling:
            timer: TimerTasks = data["timer"]
            state: FSMContext = data["state"]
            key = replace(state.key, destiny=f"throttling:{throttling}")

            if any(timer[key]):
                if (
                    isinstance(event, types.Message)
                    and secrets.randbelow(10) / 10 < ANSWER_CHANCE
                    or isinstance(event, types.CallbackQuery)
                ):
                    await self.answer(event, data)
                return None

            timer[key] = asyncio.sleep(self._tags[throttling])
        return await handler(event, data)

    async def answer(self, event: types.Message | types.CallbackQuery, data: dict) -> None:
        from core.locales.middleware import I18nContextMiddleware

        locale = await I18nContextMiddleware(self.i18n).get_locale(event, data)

        with self.i18n.context(), self.i18n.use_locale(locale):
            text = secrets.choice(
                (
                    _("Stop spamming!"),
                    _("How much information..."),
                    _("Ahhh..."),
                ),
            )

            match event:
                case types.Message():
                    content = formatting.Text(text)
                    await event.answer(**content.as_kwargs())
                case types.CallbackQuery():
                    await event.answer(text)

    def setup(self, router: Router) -> None:
        for observer in router.message, router.callback_query:
            observer.middleware(self)
