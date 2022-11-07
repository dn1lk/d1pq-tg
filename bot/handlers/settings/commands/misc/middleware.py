from typing import Callable, Dict, Any, Awaitable, Optional

from aiogram import BaseMiddleware, types

from bot.utils.database.context import DataBaseContext


class CustomCommandsMiddleware(BaseMiddleware):
    async def __call__(
            self,
            handler: Callable[[types.Message, Dict[str, Any]], Awaitable[Any]],
            event: types.Message,
            data: Dict[str, Any]
    ) -> Any:
        db: DataBaseContext = data['db']
        custom_commands: Optional[dict] = await db.get_data('commands')

        data['custom_commands'] = custom_commands or {}

        return await handler(event, data)
