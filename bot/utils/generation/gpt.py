import asyncio
import logging
from dataclasses import replace

from aiogram.fsm.storage.base import BaseStorage, StorageKey
from aiogram.utils.i18n import gettext as _

import config
from utils import database
from utils.clients import gpt_client as client
from utils.database.types import Int16
from utils.timer.tasks import TimerTasks

logger = logging.getLogger("bot.gpt")


class YandexGPT:
    def __init__(self, storage: BaseStorage, timer: TimerTasks):
        self.storage = storage
        self.timer = timer

    async def get_messages(self, key: StorageKey) -> list[dict[str, str]]:
        assert key.destiny == "gpt", f"wrong destiny key: {key.destiny}"

        data = await self.storage.get_data(key)
        return data.get("messages", [])

    async def update_messages(self, key: StorageKey, messages: list[dict[str, str]]) -> None:
        assert key.destiny == "gpt", f"wrong destiny key: {key.destiny}"

        await self.storage.update_data(key, {"messages": messages[-10:]})

        async def task():
            await asyncio.sleep(60)
            await self.storage.update_data(key, {})

        self.timer.update(key, task())

    @staticmethod
    def prepare_key(key: StorageKey) -> StorageKey:
        return replace(key, destiny="gpt")

    async def get_answer(self, gpt_settings: database.GPTSettings, key: StorageKey, owner_id: int) -> str | None:
        if gpt_settings.tokens <= 0:
            return None

        key = self.prepare_key(key)
        messages = await self.get_messages(key)

        data = {
            "modelUri": f"gpt://{config.YC_CATALOG_ID}/yandexgpt-lite",
            "completionOptions": {
                "stream": False,
                "temperature": gpt_settings.temperature,
                "maxTokens": f"{min(gpt_settings.max_tokens, max(gpt_settings.tokens, 100))}",
            },
            "messages": [
                {
                    "role": "system",
                    "text": (
                        gpt_settings.promt
                        or _(
                            "Imagine you are interacting with a user via Telegram."
                            " Respond like a AI CHAT BOT."
                            " ALWAYS USE ENGLISH."
                            ' If asked your name, CALL YOURSELF "d1pq".'
                            " Sometimes joke.",
                        )
                    ),
                },
                *messages,
            ],
        }

        async with client.post("/foundationModels/v1/completion", json=data) as response:
            data = await response.json()
            if not response.ok:
                logger.warning("bad request: %s", data)
                return None

        assistant_message = data["result"]["alternatives"][0]["message"]
        messages.append(assistant_message)

        if key.user_id != owner_id:
            gpt_settings.tokens = Int16(gpt_settings.tokens - Int16(data["result"]["usage"]["totalTokens"]))
            await gpt_settings.save()

        await self.update_messages(key, messages)

        return assistant_message["text"]
