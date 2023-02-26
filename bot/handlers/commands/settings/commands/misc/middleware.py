from typing import Callable, Any, Awaitable

from aiogram import Router, BaseMiddleware, types

from bot.utils import database


class CustomCommandsMiddleware(BaseMiddleware):
    async def __call__(
            self,
            handler: Callable[[types.TelegramObject, dict[str, Any]], Awaitable[Any]],
            event: types.Message,
            data: dict[str, Any]
    ):
        if event.text.startswith('/'):
            db: database.SQLContext = data['db']
            chat_id: int = data.get('event_chat', data['event_from_user']).id

            data['commands'] = await db.commands.get(chat_id)

        return await handler(event, data)

    def setup(self, router: Router):
        router.message.outer_middleware(self)
