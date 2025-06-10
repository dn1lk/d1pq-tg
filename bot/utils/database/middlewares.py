from collections.abc import Awaitable, Callable
from typing import TYPE_CHECKING, Any

from aiogram import BaseMiddleware, Bot, Router, enums, types
from aiogram.dispatcher.flags import get_flag

from core import helpers

from . import Model, models

if TYPE_CHECKING:
    from utils.generation import YandexGPT


class SQLGetFlagsMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[types.TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: types.TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        flag_databases: tuple[str] | str | None = get_flag(data, "database")

        if flag_databases:
            bot: Bot = data["bot"]
            chat: types.Chat | types.User | Bot = data.get("event_chat") or data.get("event_from_user") or bot

            if isinstance(flag_databases, str):
                flag_databases = (flag_databases,)

            await self.update_data(data, chat.id, *flag_databases)

        return await handler(event, data)

    async def update_data(self, data: dict[str, Any], chat_id: int, *databases: str) -> None:
        for database in databases:
            if database in data:
                continue

            data[database] = await self.get_data(chat_id, database)

    @staticmethod
    async def get_data(chat_id: int, database: str = "main_settings") -> Model:
        match database:
            case "main_settings":
                model = models.MainSettings
            case "gen_settings":
                model = models.GenSettings
            case "gpt_settings":
                model = models.GPTSettings
            case _:
                msg = f"Unknown database: {database}"
                raise TypeError(msg)

        return await model.get(chat_id=chat_id)

    def setup(self, router: Router) -> None:
        for observer in router.observers.values():
            observer.middleware(self)


class SQLGetMainMiddleware(SQLGetFlagsMiddleware):
    async def __call__(
        self,
        handler: Callable[[types.TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: types.TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        chat: types.Chat | types.User | Bot = data.get("event_chat") or data.get("event_from_user") or data["bot"]
        await self.update_data(data, chat.id, "main_settings")

        return await handler(event, data)

    def setup(self, router: Router) -> None:
        for observer in router.observers.values():
            observer.outer_middleware(self)


class SQLUpdateMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[types.TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: types.TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        if isinstance(event, types.Message):
            await self.update_query(event, data)

        result = await handler(event, data)
        return result

    @staticmethod
    async def _update_messages(
        text: str,
        data: dict[str, Any],
        gen_settings: models.GenSettings,
        gpt_settings: models.GPTSettings,
    ) -> None:
        if gpt_settings.tokens > 0:
            gpt: YandexGPT = data["gpt"]
            key = gpt.prepare_key(data["state"].key)

            messages = await gpt.get_messages(key)
            messages.append(
                {
                    "role": "user",
                    "text": text,
                },
            )

            await gpt.update_messages(key, messages)

        if gen_settings.with_messages:
            gen_settings.messages = [*gen_settings.messages[-5000:], text]

    @staticmethod
    async def _update_stickers(sticker: types.Sticker, gen_settings: models.GenSettings) -> None:
        if not (gen_settings.with_stickers and sticker.set_name):
            return

        saved_stickers = gen_settings.stickers
        if sticker.set_name not in saved_stickers:
            gen_settings.stickers = [*saved_stickers[-4:], sticker.set_name]

    @classmethod
    async def update_query(cls, event: types.Message, data: dict[str, Any]) -> None:
        main_settings: models.MainSettings = data["main_settings"]
        gen_settings: models.GenSettings = data.setdefault(
            "gen_settings",
            await models.GenSettings.get(chat_id=event.chat.id),
        )
        gpt_settings: models.GPTSettings = data.setdefault(
            "gpt_settings",
            await models.GPTSettings.get(chat_id=event.chat.id),
        )

        text = helpers.get_text(event)
        if text:
            await cls._update_messages(text, data, gen_settings, gpt_settings)
        elif event.sticker:
            await cls._update_stickers(event.sticker, gen_settings)

        if main_settings.with_members and event.chat.type != enums.ChatType.PRIVATE:
            saved_members = main_settings.members

            if event.from_user.id not in saved_members:
                main_settings.members = [*saved_members, event.from_user.id]

        if main_settings.columns_changed:
            await main_settings.save()
        if gen_settings.columns_changed:
            await gen_settings.save()

    def setup(self, router: Router) -> None:
        router.message.outer_middleware(self)
