import asyncio
from dataclasses import dataclass
from typing import Awaitable, Callable, Any

from aiogram import Bot, Dispatcher, BaseMiddleware, types
from aiogram.dispatcher.flags import get_flag
from aiogram.utils.chat_action import ChatActionMiddleware

from utils import markov
from utils.database.context import DataBaseContext


class DataMiddleware(BaseMiddleware):
    async def __call__(
            self,
            handler: Callable[
                [types.Message | types.CallbackQuery | types.ChatMemberUpdated, dict[str, Any]],
                Awaitable[Any]
            ],
            event: types.Message | types.CallbackQuery | types.ChatMemberUpdated,
            data: dict[str, Any]
    ):
        db: DataBaseContext = data['db']
        flag_data: str | tuple | None = get_flag(data, 'data')

        if flag_data:
            async def get_data(column: str):
                value = await db.get_data(column)

                if column == 'chance':
                    bot: Bot = data['bot']
                    value = round(value / await bot.get_chat_member_count(data['event_chat'].id) * 100, 2)

                if value:
                    data[column] = value

            if isinstance(flag_data, str):
                await get_data(flag_data)
            else:
                for key in flag_data:
                    await get_data(key)

        if get_flag(data, 'throttling') == 'gen':
            data['messages'] = await db.get_data('messages')

        result = await handler(event, data)

        if data['event_chat'].type != 'private':
            members: list | None = data.get('members', await db.get_data('members'))

            if members and data['event_from_user'].id not in members:
                await db.update_data(members=[*members, data['event_from_user'].id])

        return result


class ThrottlingMiddleware(BaseMiddleware):
    tasks = {}
    timeouts = {
        'gen': 3,
    }

    def __setitem__(self, name: str, task: asyncio.Task):
        self.tasks[name] = task
        task.set_name(name)
        task.add_done_callback(lambda _: self.tasks.pop(name))

    def __getitem__(self, name):
        return self.tasks.get(name)

    async def __call__(
            self,
            handler: Callable[[types.Message, dict[str, Any]], Awaitable[Any]],
            event: types.Message,
            data: dict[str, Any],
    ):
        throttling = get_flag(data, 'throttling')

        if throttling:
            chat_id: int = data.get('event_chat', data['event_from_user']).id
            task_name = f'{chat_id}:{throttling}'

            if task_name in self.tasks:
                return

            self[task_name] = asyncio.create_task(self.timer(self.timeouts[throttling]))

        return await handler(event, data)

    @staticmethod
    async def timer(delay: int):
        await asyncio.sleep(delay)


class UnhandledMiddleware(BaseMiddleware):
    async def __call__(
            self,
            handler: Callable[[types.Message, dict[str, Any]], Awaitable[Any]],
            event: types.Message,
            data: dict[str, Any]
    ):
        result = await handler(event, data)

        db: DataBaseContext = data['db']

        if event.text:
            messages = data.get('messages', await db.get_data('messages'))
            new_messages = markov.set_data(event.text, messages)

            if new_messages != messages:
                await db.set_data(messages=new_messages)

        elif event.sticker and event.sticker.set_name != 'uno_by_bp1lh_bot':
            stickers: list[str] = await db.get_data('stickers')

            if event.sticker.set_name not in stickers:
                stickers.append(event.sticker.set_name)
                await db.set_data(stickers=stickers[-3:])

        return result


@dataclass
class Middleware:
    inner: BaseMiddleware = None
    outer: BaseMiddleware = None
    observers: str | tuple = 'update'


def setup(dp: Dispatcher):
    from bot import config

    from handlers.settings.commands import CustomCommandsMiddleware
    from locales.middleware import I18nContextMiddleware
    from utils.database.middleware import DataBaseContextMiddleware
    from utils.timer.middleware import TimerMiddleware

    middlewares = (
        Middleware(outer=DataBaseContextMiddleware()),
        Middleware(outer=CustomCommandsMiddleware(), observers=('message', 'callback_query')),
        Middleware(inner=ThrottlingMiddleware(), observers='message'),
        Middleware(inner=ChatActionMiddleware(), observers=('message', 'callback_query')),
        Middleware(inner=DataMiddleware(), observers=('message', 'callback_query', 'chat_member')),
        Middleware(inner=I18nContextMiddleware(i18n=config.i18n)),
        Middleware(inner=TimerMiddleware(), observers=('message', 'callback_query', 'chat_member')),
        Middleware(outer=UnhandledMiddleware(), observers='message'),
    )

    def register_middleware(obs: str):
        register = dp.observers[obs]

        if middleware.inner:
            register.middleware(middleware.inner)
        else:
            register.outer_middleware(middleware.outer)

    for middleware in middlewares:
        if isinstance(middleware.observers, str):
            register_middleware(middleware.observers)
        else:
            for observer in middleware.observers:
                register_middleware(observer)
