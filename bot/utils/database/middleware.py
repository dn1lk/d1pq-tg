from typing import Callable, Dict, Any, Awaitable

from aiogram import BaseMiddleware, Bot, types
from aiogram.dispatcher.fsm.storage.base import BaseStorage, StorageKey
from asyncpg import Pool

from .context import DataBaseContext


class DataBaseContextMiddleware(BaseMiddleware):
    def __init__(self, storage: BaseStorage, pool_db: Pool):
        self.storage = storage
        self.pool_db = pool_db

    async def __call__(
            self,
            handler: Callable[[types.TelegramObject, Dict[str, Any]], Awaitable[Any]],
            event: types.TelegramObject,
            data: Dict[str, Any],
    ) -> Any:
        bot: Bot = data["bot"]
        chat_id: int = data.get("event_chat", data["event_from_user"]).id
        data["db"] = self.get_context(bot, chat_id)
        return await handler(event, data)

    def get_context(
            self,
            bot: Bot,
            chat_id: int,
            destiny: str = 'database',
    ) -> DataBaseContext:
        return DataBaseContext(
            bot=bot,
            pool_db=self.pool_db,
            storage=self.storage,
            key=StorageKey(
                bot_id=bot.id,
                chat_id=chat_id,
                user_id=chat_id,
                destiny=destiny,
            )
        )
