import logging
from dataclasses import dataclass
from json import dumps, loads
from typing import Dict, Any, Awaitable, Callable, Union, Optional

from aiogram import Bot, BaseMiddleware, types, Dispatcher
from aiogram.dispatcher.flags.getter import get_flag
from aiogram.dispatcher.fsm.context import FSMContext
from aiogram.utils.chat_action import ChatActionMiddleware
from aiogram.utils.i18n.middleware import SimpleI18nMiddleware

from utils import markov


class InnerDataMiddleware(BaseMiddleware):
    async def __call__(
            self,
            handler: Callable[[Union[types.Message, types.CallbackQuery], Dict[str, Any]], Awaitable[Any]],
            event: Union[types.Message, types.CallbackQuery],
            data: Dict[str, Any]
    ) -> Any:
        bot: Bot = data['bot']
        state: Optional[FSMContext] = data.get('state')

        flag_data: Union[str, list] = get_flag(data, 'data')

        if flag_data:
            if isinstance(flag_data, str):
                flag_data = [flag_data]

            for key in flag_data:
                value = await bot.sql.get_data(data['event_chat'].id, key, None if key == 'messages' else state)

                if isinstance(value, str) and key in ('members', 'commands'):
                    value = loads(value)
                elif key == 'chance':
                    value = round(float(value) / await bot.get_chat_member_count(data['event_chat'].id) * 100, 2)

                data[key] = value

            if get_flag(data, 'gen') and ['DECLINE'] != data.get('messages'):
                if isinstance(event, types.Message) and event.text:
                    messages = markov.set_data(event.text, data.get('messages'))
                    if messages:
                        data['messages'] = messages

                        await bot.sql.set_data(data['event_chat'].id, 'messages', messages)

        result = await handler(event, data)

        if data['event_chat'].type != 'private':
            members: Optional[Union[str, dict]] = data.get(
                'members',
                await bot.sql.get_data(data['event_chat'].id, 'members', state)
            )

            if members:
                if isinstance(members, str):
                    members = loads(members)
                if not members.get(str(data['event_from_user'].id)):
                    members[str(data['event_from_user'].id)] = data['event_from_user'].first_name
                    await bot.sql.update_data(data['event_chat'].id, 'members', dumps(members), state)

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


class LocaleMiddleware(SimpleI18nMiddleware):
    from aiogram.utils.i18n import I18n
    import config

    def __init__(self, i18n: I18n = config.i18n):
        super().__init__(i18n)

    async def get_locale(self, event: types.Update, data: Dict[str, Any]) -> str:
        locale = await data['bot'].sql.get_data(
            (data.get('event_chat', data['event_from_user'])).id,
            'locales',
            data.get('state')
        )

        if not locale:
            locale = await super().get_locale(event=event, data=data)

        return locale


class OuterDataMiddleware(BaseMiddleware):
    async def __call__(
            self,
            handler: Callable[[Union[types.Message, types.CallbackQuery], Dict[str, Any]], Awaitable[Any]],
            event: Union[types.Message, types.CallbackQuery],
            data: Dict[str, Any]
    ) -> Any:
        bot: Bot = data['bot']
        state: Optional[FSMContext] = data.get('state')

        commands: Optional[str] = await bot.sql.get_data(
            (data.get('event_chat', data['event_from_user'])).id,
            'commands',
            state,
        )

        if commands:
            data['commands'] = loads(commands)

        result = await handler(event, data)

        if isinstance(event, types.Message):
            if event.sticker:
                stickers: list = await bot.sql.get_data(data['event_chat'].id, 'stickers', state)

                if event.sticker.set_name not in stickers:
                    stickers.insert(0, event.sticker.set_name)
                    await bot.sql.set_data(data['event_chat'].id, 'stickers', stickers[slice(3)], state)

        from aiogram.dispatcher.event.bases import UNHANDLED
        if result is UNHANDLED:
            if isinstance(event, types.Message) and event.text:
                messages = markov.set_data(
                    event.text,
                    data.get('messages', await bot.sql.get_data(data['event_chat'].id, 'messages')),
                )
                if messages:
                    await bot.sql.set_data(data['event_chat'].id, 'messages', messages)

        return result


@dataclass
class Middleware:
    inner: Optional[BaseMiddleware] = None
    outer: Optional[BaseMiddleware] = None
    observers: Optional[list[str]] = 'update',


def setup(dp: Dispatcher):
    middlewares = (
        Middleware(inner=LogMiddleware()),
        Middleware(inner=ChatActionMiddleware()),
        Middleware(inner=InnerDataMiddleware(), observers=['message', 'callback_query']),
        Middleware(outer=LocaleMiddleware()),
        Middleware(outer=OuterDataMiddleware(), observers=['message', 'callback_query']),
    )

    for middleware in middlewares:
        for observer in middleware.observers:
            register = dp.observers[observer]

            if middleware.inner:
                register.middleware(middleware.inner)
            elif middleware.outer:
                register.outer_middleware(middleware.outer)

    return dp
