from typing import Callable, Any, Awaitable

from aiogram import BaseMiddleware, types
from aiogram.dispatcher.flags import get_flag

from .. import database


class SQLGetMiddleware(BaseMiddleware):
    async def __call__(
            self,
            handler: Callable[[types.TelegramObject, dict[str, Any]], Awaitable[Any]],
            event: types.TelegramObject,
            data: dict[str, Any],
    ):
        sql: str | tuple | None = get_flag(data, 'sql')

        if sql:
            db: database.SQLContext = data['db']
            chat_id: int = data.get('event_chat', data['event_from_user']).id

            if isinstance(sql, str):
                data[sql] = await db[sql].get(chat_id)
            else:
                for key in sql:
                    data[key] = await db[key].get(chat_id)

        return await handler(event, data)


class SQLUpdateMiddleware(BaseMiddleware):
    async def __call__(
            self,
            handler: Callable[[types.TelegramObject, dict[str, Any]], Awaitable[Any]],
            event: types.TelegramObject,
            data: dict[str, Any],
    ):
        result = await handler(event, data)

        if isinstance(event, types.Message) and not event.left_chat_member:
            await self.update_sql(event, data)

        return result

    @staticmethod
    async def update_sql(event: types.Message, data: dict[str, Any]):
        db: database.SQLContext = data['db']
        text = event.text or event.caption or (event.poll.question if event.poll else None)

        if text:
            from .. import markov
            await markov.set_messages(db, text, event.chat.id, data.get('messages'))

        elif event.sticker:
            from .. import sticker
            await sticker.set_stickers(db, event.sticker.set_name, event.chat.id, data.get('stickers'))

        if event.chat.type != 'private':
            members: list[int] = data.get('members', await db.members.get(event.chat.id))

            if members and event.from_user.id not in members:
                await db.members.cat(event.chat.id, [event.from_user.id])
