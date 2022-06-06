from typing import Callable, Dict, Any, Awaitable

from aiogram import BaseMiddleware, Bot, types
from aiogram.dispatcher.fsm.storage.base import DEFAULT_DESTINY, BaseStorage, StorageKey
from asyncpg import Pool

from .context import DataBaseContext


class DataBaseContextMiddleware(BaseMiddleware):
    def __init__(self, storage: BaseStorage):
        self.storage = storage

    async def __call__(
        self,
        handler: Callable[[types.TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: types.TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        bot: Bot = data["bot"]
        chat: types.Chat = data.get("event_chat", data["event_from_user"])
        dp_pool: Pool = data["db_pool"]

        data["db"] = self.get_context(bot, dp_pool, chat.id)

        return await handler(event, data)

    def get_context(
        self,
        bot: Bot,
        dp_pool: Pool,
        chat_id: int,
        destiny: str = DEFAULT_DESTINY,
    ) -> DataBaseContext:
        return DataBaseContext(
            bot=bot,
            dp_pool=dp_pool,
            storage=self.storage,
            key=StorageKey(
                user_id=chat_id,
                chat_id=chat_id,
                bot_id=bot.id,
                destiny=destiny,
            )
        )
