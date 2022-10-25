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
        if 'custom_commands' not in data:
            db: DataBaseContext = data['db']
            custom_commands: Optional[dict] = await db.get_data('commands')

            if custom_commands:
                data['custom_commands'] = custom_commands

        return await handler(event, data)
