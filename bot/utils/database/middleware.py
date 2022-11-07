from typing import Callable, Dict, Any, Awaitable

from aiogram import BaseMiddleware, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.base import StorageKey
from asyncpg import Pool

from .context import DataBaseContext


class DataBaseContextMiddleware(BaseMiddleware):
    async def __call__(
            self,
            handler: Callable[[types.TelegramObject, Dict[str, Any]], Awaitable[Any]],
            event: types.TelegramObject,
            data: Dict[str, Any],
    ) -> Any:
        pool_db: Pool = data["pool_db"]
        state: FSMContext = data["state"]

        data["db"] = self.get_context(pool_db, state)
        return await handler(event, data)

    @staticmethod
    def get_context(
            pool_db: Pool,
            state: FSMContext,
            destiny: str = 'database',
    ) -> DataBaseContext:
        return DataBaseContext(
            bot=state.bot,
            key=StorageKey(
                bot_id=state.key.bot_id,
                chat_id=state.key.chat_id,
                user_id=state.key.chat_id,
                destiny=destiny,
            ),
            storage=state.storage,
            pool_db=pool_db,
        )
