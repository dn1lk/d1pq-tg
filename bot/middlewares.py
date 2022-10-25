import asyncio
import logging
from dataclasses import dataclass
from typing import Dict, Any, Awaitable, Callable, Union, Optional

from aiogram import Bot, Dispatcher, BaseMiddleware, types
from aiogram.dispatcher.flags import get_flag, extract_flags
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.base import StorageKey, BaseStorage
from aiogram.utils.chat_action import ChatActionMiddleware

from utils import markov
from utils.database.context import DataBaseContext


class DataMiddleware(BaseMiddleware):
    async def __call__(
            self,
            handler: Callable[[Union[types.Message, types.CallbackQuery], Dict[str, Any]], Awaitable[Any]],
            event: Union[types.Message, types.CallbackQuery],
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

                if value:
                    data[key] = value

            if 'gen' in extract_flags(data).values() and event.text:
                messages = markov.set_data(event.text, data.get('messages'))

                if messages:
                    data['messages'] = messages
                    await db.set_data(messages=messages)

        result = await handler(event, data)

        if data['event_chat'].type != 'private':
            members: Optional[list] = data.get('members', await db.get_data('members'))

            if members and data['event_from_user'].id not in members:
                members.append(data['event_from_user'].id)
                await db.update_data(members=members)

        return result


class LogMiddleware(BaseMiddleware):
    async def __call__(
            self,
            handler: Callable[[types.Update, Dict[str, Any]], Awaitable[Any]],
            event: types.Update,
            data: Dict[str, Any]
    ) -> Any:
        logging.debug(f'New event - {event.event_type}:\n{event.event}')
        return await handler(event, data)


class ThrottlingMiddleware(BaseMiddleware):
    timeouts = {
        'gen': 3,
    }

    def __init__(self, storage: BaseStorage):
        self.storage = storage

    async def __call__(
            self,
            handler: Callable[[types.TelegramObject, Dict[str, Any]], Awaitable[Any]],
            event: types.TelegramObject,
            data: Dict[str, Any],
    ) -> Any:
        throttling = get_flag(data, 'throttling')

        if throttling:
            bot: Bot = data['bot']
            chat_id: int = data.get('event_chat', data['event_from_user']).id
            state = self.get_context(bot, chat_id)

            if throttling in await state.get_data():
                return

            await state.update_data({throttling: True})
            self.timer(state, throttling)

        return await handler(event, data)

    def get_context(
            self,
            bot: Bot,
            chat_id: int,
            destiny: str = 'throttling',
    ) -> FSMContext:
        return FSMContext(
            bot=bot,
            storage=self.storage,
            key=StorageKey(
                user_id=chat_id,
                chat_id=chat_id,
                bot_id=bot.id,
                destiny=destiny,
            ),
        )

    def timer(self, state: FSMContext, key: str):
        async def waiter():
            await asyncio.sleep(self.timeouts[key])
            data = await state.get_data()

            if data.pop(key, None):
                await state.set_data(data)

        asyncio.create_task(waiter(), name=f'{state.key.destiny}:{state.key.chat_id}')


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

    from locales.middleware import I18nContextMiddleware
    from utils.database.middleware import DataBaseContextMiddleware

    middlewares = (
        Middleware(inner=ThrottlingMiddleware(dp.storage), observers='message'),
        Middleware(inner=ChatActionMiddleware()),
        Middleware(inner=DataMiddleware(), observers={'message', 'callback_query'}),
        Middleware(outer=LogMiddleware()),
        Middleware(outer=DataBaseContextMiddleware(storage=dp.storage, pool_db=dp['pool_db'])),
        Middleware(outer=I18nContextMiddleware(i18n=config.i18n)),
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
