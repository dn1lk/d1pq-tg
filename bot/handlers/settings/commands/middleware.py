from typing import Callable, Any, Awaitable

from aiogram import BaseMiddleware, types
from aiogram.dispatcher.flags import get_flag

from bot.utils import database


class CustomCommandsMiddleware(BaseMiddleware):
    async def __call__(
            self,
            handler: Callable[[types.Message, dict[str, Any]], Awaitable[Any]],
            event: types.Message,
            data: dict[str, Any]
    ):
        commands: tuple[str] | None = get_flag(data, 'commands')

        if commands:
            db: database.SQLContext = data['db']
            chat_id: int = data.get('event_chat', data['event_from_user']).id

            data['custom_commands'] = await db.commands.get(chat_id)

        return await handler(event, data)
