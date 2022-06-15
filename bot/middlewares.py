import logging
from dataclasses import dataclass
from typing import Dict, Any, Awaitable, Callable, Union, Optional

from aiogram import Bot, Dispatcher, BaseMiddleware, types
from aiogram.dispatcher.flags.getter import get_flag
from aiogram.dispatcher.fsm.context import FSMContext
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

        flag_data: Optional[Union[str, tuple]] = get_flag(data, 'data')

        if flag_data:
            if isinstance(flag_data, str):
                flag_data = flag_data,

            for key in flag_data:
                value = await db.get_data(key)

                if key == 'chance':
                    bot: Bot = data['bot']
                    value = round(float(value) / await bot.get_chat_member_count(data['event_chat'].id) * 100, 2)

                if value:
                    data[key] = value

            if get_flag(data, 'gen') and event.text:
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
        logging.debug(f'New event - {event.event_type}:\n{event}')
        return await handler(event, data)


class ThrottlingMiddleware(BaseMiddleware):
    timeouts = {
        'gen': 1,
    }

    async def __call__(
            self,
            handler: Callable[[types.Message, Dict[str, Any]], Awaitable[Any]],
            event: types.Message,
            data: Dict[str, Any],
    ) -> Any:
        state: FSMContext = data.get('state')
        throttling = get_flag(data, 'throttling')

        if state and throttling:
            throttling = f'throttling:{throttling}'

            if (await state.get_data()).get(throttling):
                return
            else:
                await state.update_data({throttling: True})
                state.timer(timeout=self.timeouts[throttling.split(':')[-1]], throttling=throttling)

        return await handler(event, data)


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

            if event.sticker:
                stickers = await db.get_data('stickers')

                if event.sticker.set_name not in stickers:
                    stickers.insert(0, event.sticker.set_name)
                    await db.set_data(stickers=stickers[slice(3)])

            elif event.text:
                messages = markov.set_data(
                    event.text,
                    data.get('messages', await db.get_data('messages')),
                )
                if messages:
                    await db.set_data(messages=messages)

        return result


@dataclass
class Middleware:
    inner: Optional[BaseMiddleware] = None
    outer: Optional[BaseMiddleware] = None
    observers: Optional[tuple] = 'update',


def setup(dp: Dispatcher):
    from bot import config

    from locales.middleware import I18nContextMiddleware
    from utils.database.middleware import DataBaseContextMiddleware

    middlewares = (
        Middleware(inner=ThrottlingMiddleware(), observers=('message',)),
        Middleware(inner=ChatActionMiddleware()),
        Middleware(inner=DataMiddleware(), observers=('message', 'callback_query')),
        # Middleware(outer=LogMiddleware()),
        Middleware(outer=DataBaseContextMiddleware(storage=dp.storage)),
        Middleware(outer=I18nContextMiddleware(i18n=config.i18n)),
        Middleware(outer=UnhandledMiddleware(), observers=('message',)),
    )

    for middleware in middlewares:
        for observer in middleware.observers:
            register = dp.observers[observer]

            if middleware.inner:
                register.middleware(middleware.inner)
            elif middleware.outer:
                register.outer_middleware(middleware.outer)
