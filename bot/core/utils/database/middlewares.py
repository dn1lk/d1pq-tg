from typing import Callable, Any, Awaitable

from aiogram import Bot, Router, BaseMiddleware, types
from aiogram.dispatcher.flags import get_flag
from aiogram.fsm.storage.base import StorageKey

from core import helpers
from . import models
from ..generation import YandexGPT


class SQLGetFlagsMiddleware(BaseMiddleware):
    async def __call__(
            self,
            handler: Callable[[types.TelegramObject, dict[str, Any]], Awaitable[Any]],
            event: types.TelegramObject,
            data: dict[str, Any],
    ):
        flag_databases: tuple[str] | str | None = get_flag(data, 'database')

        if flag_databases:
            bot: Bot = data['bot']
            chat: types.Chat | types.User | Bot = data.get('event_chat') or data.get('event_from_user') or bot

            if isinstance(flag_databases, str):
                flag_databases = flag_databases,

            await self.update_data(data, chat.id, *flag_databases)

        return await handler(event, data)

    async def update_data(self, data: dict[str, Any], chat_id: int, *databases: str):
        data.update({database: await self.get_data(chat_id, database) for database in databases})

    @staticmethod
    async def get_data(chat_id: int, database: str = 'main_settings'):
        match database:
            case 'main_settings':
                model = models.MainSettings
            case 'gen_settings':
                model = models.GenSettings
            case 'gpt_settings':
                model = models.GPTSettings
            case _:
                raise TypeError

        return await model.get(chat_id=chat_id)

    def setup(self, router: Router):
        for observer in router.observers.values():
            observer.middleware(self)


class SQLGetMainMiddleware(SQLGetFlagsMiddleware):
    async def __call__(
            self,
            handler: Callable[[types.TelegramObject, dict[str, Any]], Awaitable[Any]],
            event: types.TelegramObject,
            data: dict[str, Any],
    ):
        bot: Bot = data['bot']
        chat: types.Chat | types.User | Bot = data.get('event_chat') or data.get('event_from_user') or bot

        await self.update_data(data, chat.id)
        return await handler(event, data)

    async def update_data(self, data: dict[str, Any], chat_id: int, *databases: str):
        await super().update_data(data, chat_id, 'main_settings')

    def setup(self, router: Router):
        for observer in router.observers.values():
            observer.outer_middleware(self)


class SQLUpdateMiddleware(BaseMiddleware):
    async def __call__(
            self,
            handler: Callable[[types.TelegramObject, dict[str, Any]], Awaitable[Any]],
            event: types.Message,
            data: dict[str, Any],
    ):
        await self.update_sql(event, data)
        result = await handler(event, data)

        return result

    @staticmethod
    async def update_sql(event: types.Message, data: dict[str, Any]):
        main_settings: models.MainSettings = data['main_settings']
        gen_settings: models.GenSettings = (
                data.get('gen_settings')
                or await models.GenSettings.get(chat_id=event.chat.id)
        )
        gpt_settings: models.GPTSettings = (
            data.get('gpt_settings')
            or await models.GPTSettings.get(chat_id=event.chat.id)
        )

        main_updated = False
        gen_updated = False

        text = helpers.get_text(event)
        if text:
            if gpt_settings.tokens > 0:
                gpt: YandexGPT = data['gpt']
                key: StorageKey = gpt.get_key(data['state'].key)

                messages = await gpt.get_messages(key)
                messages.append({
                    "role": "user",
                    "text": text
                })

                await gpt.update_messages(key, messages)

            if gen_settings.messages is not None:
                gen_settings.messages.append(text)

                if len(gen_settings.messages) > 5000:
                    del gen_settings.messages[:1000]

                gen_updated = True
        elif event.sticker and gen_settings.stickers is not None:
            if event.sticker.set_name not in gen_settings.stickers:
                gen_settings.stickers.append(event.sticker.set_name)

                if len(gen_settings.stickers) > 5:
                    del gen_settings.stickers[0]

                gen_updated = True

        if main_settings.members is not None:
            if event.from_user.id not in main_settings.members:
                main_settings.members.append(event.from_user.id)
                main_updated = True

        if main_updated:
            await main_settings.save()
        if gen_updated:
            await gen_settings.save()

    def setup(self, router: Router):
        router.message.outer_middleware(self)
