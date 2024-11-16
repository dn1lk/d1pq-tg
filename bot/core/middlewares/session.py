import asyncio
import time
from collections import defaultdict
from typing import cast

from aiogram import Bot, exceptions, loggers, methods
from aiogram.client.session.middlewares.base import BaseRequestMiddleware, NextRequestMiddlewareType
from aiogram.methods.base import Response, TelegramMethod, TelegramType


class SessionRateLimiterMiddleware(BaseRequestMiddleware):
    RATE = 25
    MAX_TOKENS = 30

    def __init__(self) -> None:
        self.tokens = self.MAX_TOKENS
        self.updated_at = time.monotonic()

        self._tasks: set[asyncio.Task] = set()
        self._locks: dict[str, asyncio.Lock] = defaultdict(asyncio.Lock)

    async def __call__(
        self,
        make_request: NextRequestMiddlewareType[TelegramType],
        bot: Bot,
        method: TelegramMethod[TelegramType],
    ) -> Response[TelegramType]:
        if isinstance(method, methods.SendMessage):
            await self.wait_for_token()

            lock = self._locks[f"{method.chat_id}"]
            await lock.acquire()

            try:
                method = cast(TelegramMethod[TelegramType], method)
                return await make_request(bot, method)
            finally:
                self.wait_for_chat(lock)

        return await make_request(bot, method)

    async def wait_for_token(self) -> None:
        while self.tokens <= 1:
            now = time.monotonic()
            time_since_update = now - self.updated_at
            new_tokens = time_since_update * self.RATE
            if self.tokens + new_tokens >= 1:
                self.tokens = min(self.tokens + new_tokens, self.MAX_TOKENS)
                self.updated_at = now

            await asyncio.sleep(1)

        self.tokens -= 1

    def wait_for_chat(self, lock: asyncio.Lock) -> None:
        async def timer() -> None:
            await asyncio.sleep(1)
            lock.release()

        task = asyncio.create_task(timer())
        self._tasks.add(task)

        task.add_done_callback(self._tasks.remove)

    def setup(self, bot: Bot) -> None:
        bot.session.middleware(self)


class SessionRetryMiddleware(BaseRequestMiddleware):
    async def __call__(
        self,
        make_request: NextRequestMiddlewareType[TelegramType],
        bot: Bot,
        method: TelegramMethod[TelegramType],
    ) -> Response[TelegramType]:
        for _ in range(3):
            try:
                return await make_request(bot, method)
            except exceptions.TelegramRetryAfter as err:
                loggers.middlewares.error(err.message)
                await asyncio.sleep(err.retry_after)

        raise RuntimeError

    def setup(self, bot: Bot) -> None:
        bot.session.middleware(self)
