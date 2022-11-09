import asyncio
from dataclasses import dataclass
from typing import Dict, Any, Awaitable, Callable, Union, Optional

from aiogram import Bot, Dispatcher, BaseMiddleware, types
from aiogram.dispatcher.flags import get_flag
from aiogram.utils.chat_action import ChatActionMiddleware

from utils import markov
from utils.database.context import DataBaseContext


class DataMiddleware(BaseMiddleware):
    async def __call__(
            self,
            handler: Callable[
                [types.Message | types.CallbackQuery | types.ChatMemberUpdated, Dict[str, Any]],
                Awaitable[Any]
            ],
            event: types.Message | types.CallbackQuery | types.ChatMemberUpdated,
            data: Dict[str, Any]
    ) -> Any:
        db: DataBaseContext = data['db']
        flag_data: Optional[Union[str, set]] = get_flag(data, 'data')

        if flag_data:
            if isinstance(flag_data, str):
                flag_data = {flag_data}

            for key in flag_data:
                value = await db.get_data(key)

                if key == 'chance':
                    bot: Bot = data['bot']
                    value = round(value / await bot.get_chat_member_count(data['event_chat'].id) * 100, 2)

                data[key] = value

        if get_flag(data, 'throttling') == 'gen':
            messages = await db.get_data('messages')
            new_messages = data['messages'] = markov.set_data(event.text, messages)

            if new_messages != messages:
                await db.set_data(messages=new_messages)

        result = await handler(event, data)

        if data['event_chat'].type != 'private':
            members: Optional[list] = data.get('members', await db.get_data('members'))

            if members and data['event_from_user'].id not in members:
                await db.update_data(members=[*members, data['event_from_user'].id])

        return result


class ThrottlingMiddleware(BaseMiddleware):
    tasks = {}
    timeouts = {
        'gen': 3,
    }

    def __setitem__(self, name: str, task: asyncio.Task):
        def del_task(t: asyncio.Task):
            if t is self[name]:
                del self.tasks[name]

        self.tasks[name] = task
        task.set_name(name)
        task.add_done_callback(del_task)

    def __getitem__(self, name):
        return self.tasks.get(name)

    def __delitem__(self, name):
        self.tasks[name].cancel()

    async def __call__(
            self,
            handler: Callable[[types.TelegramObject, Dict[str, Any]], Awaitable[Any]],
            event: types.TelegramObject,
            data: Dict[str, Any],
    ) -> Any:
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
            handler: Callable[[types.Message, Dict[str, Any]], Awaitable[Any]],
            event: types.Message,
            data: Dict[str, Any]
    ) -> Any:
        result = await handler(event, data)

        from aiogram.dispatcher.event.bases import UNHANDLED

        if result is UNHANDLED:
            db: DataBaseContext = data['db']

            if event.text:
                messages = markov.set_data(
                    event.text,
                    data.get('messages', await db.get_data('messages')),
                )
                if messages:
                    await db.set_data(messages=messages)

            elif event.sticker and event.sticker.set_name != 'uno_by_bp1lh_bot':
                stickers: list[str] = await db.get_data('stickers')

                if event.sticker.set_name not in stickers:
                    stickers.append(event.sticker.set_name)
                    await db.set_data(stickers=stickers[-3:])

        return result


@dataclass
class Middleware:
    inner: Optional[BaseMiddleware] = None
    outer: Optional[BaseMiddleware] = None
    observers: Optional[Union[str, set]] = 'update'


def setup(dp: Dispatcher):
    from bot import config

    from handlers.settings.commands import CustomCommandsMiddleware
    from locales.middleware import I18nContextMiddleware
    from utils.database.middleware import DataBaseContextMiddleware

    middlewares = (
        Middleware(outer=DataBaseContextMiddleware()),
        Middleware(outer=CustomCommandsMiddleware(), observers={'message', 'callback_query'}),
        Middleware(inner=ThrottlingMiddleware(), observers='message'),
        Middleware(inner=ChatActionMiddleware()),
        Middleware(inner=DataMiddleware(), observers={'message', 'callback_query', 'chat_member'}),
        Middleware(inner=I18nContextMiddleware(i18n=config.i18n)),
        Middleware(outer=UnhandledMiddleware(), observers='message'),
    )

    for middleware in middlewares:
        if isinstance(middleware.observers, str):
            middleware.observers = {middleware.observers}

        for observer in middleware.observers:
            register = dp.observers[observer]

            if middleware.inner:
                register.middleware(middleware.inner)
            else:
                register.outer_middleware(middleware.outer)
