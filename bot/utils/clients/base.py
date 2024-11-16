import asyncio
import logging
import secrets
from abc import abstractmethod
from collections.abc import Callable
from contextlib import _AsyncGeneratorContextManager, asynccontextmanager
from functools import wraps
from typing import ClassVar

import aiohttp

from utils import exceptions

logger = logging.getLogger("bot.clients")

MAX_RETRY_COUNT = 2


def errorasynccontextmanager(
    func: Callable[..., aiohttp.client._RequestContextManager],
) -> Callable[..., _AsyncGeneratorContextManager[aiohttp.ClientResponse]]:
    _locker = asyncio.Lock()

    @asynccontextmanager
    @wraps(func)
    async def wrapper(*args: object, **kwargs: object):
        retry_count = 0
        extra = dict(zip(func.__code__.co_varnames, args, strict=False)) | kwargs

        while True:
            try:
                async with func(*args, **kwargs) as response:
                    yield response
                    break

            except (TimeoutError, aiohttp.ClientError) as e:
                retry_count += 1
                if retry_count > MAX_RETRY_COUNT:
                    logger.exception("finish retrying", extra=extra)
                    raise exceptions.RequestError from e

                delay = secrets.randbelow(3)
                delay += retry_count**retry_count

                async with _locker:
                    logger.warning("failed - %s. retry after: %f", e, delay, extra=extra)
                    await asyncio.sleep(delay)

    return wrapper


class BaseClient:
    _session: ClassVar[aiohttp.ClientSession | None] = None
    _instance: ClassVar["BaseClient | None"] = None

    def __new__(cls) -> "BaseClient":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @classmethod
    @abstractmethod
    async def _setup(cls) -> None:
        cls._session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=2 * 60),
        )

    @classmethod
    async def setup(cls) -> None:
        assert cls._session is None, "session has already configured"
        await cls._setup()

    @classmethod
    async def close(cls) -> None:
        assert cls._session is not None, "session not configured"
        await cls._session.close()

    @classmethod
    @errorasynccontextmanager
    @wraps(aiohttp.ClientSession.get)
    def get(cls, url: str, **kwargs) -> aiohttp.client._RequestContextManager:
        assert cls._session is not None, "session not configured"
        logger.debug("GET-query: %s", url, extra=kwargs)

        return cls._session.get(url, **kwargs)

    @classmethod
    @errorasynccontextmanager
    @wraps(aiohttp.ClientSession.post)
    def post(cls, url: str, **kwargs) -> aiohttp.client._RequestContextManager:
        assert cls._session is not None, "session not configured"
        logger.debug("POST-query: %s", url, extra=kwargs)

        return cls._session.post(url, **kwargs)
