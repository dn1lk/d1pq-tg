import asyncio
import logging
from dataclasses import replace

import aiohttp
import ydb
from aiogram.fsm.storage.base import BaseStorage, StorageKey
from aiogram.utils.i18n import gettext as _

import config
from core.utils import database
from core.utils.timer import TimerTasks

logger = logging.getLogger('gpt')


class YandexGPT:
    url = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"
    data = {
        "modelUri": f"gpt://{config.YC_CATALOG_ID}/yandexgpt-lite",
    }

    def __init__(self, session: aiohttp.ClientSession, storage: BaseStorage):
        self.session = session
        self.storage = storage
        self.timer = TimerTasks()

        self.credentials = ydb.iam.ServiceAccountCredentials.from_file(
            config.YC_SERVICE_ACCOUNT_FILE_CREDENTIALS,
        )

    @staticmethod
    def get_key(key: StorageKey) -> StorageKey:
        return replace(key, destiny='gpt')

    async def get_messages(self, key: StorageKey) -> list[dict[str, str]]:
        assert key.destiny == 'gpt', f'wrong destiny key: {key.destiny}'

        data = await self.storage.get_data(key)
        return data.get('messages', [])

    async def update_messages(self, key: StorageKey, messages: list[dict[str, str]] | None):
        assert key.destiny == 'gpt', f'wrong destiny key: {key.destiny}'

        if len(messages) > 10:
            del messages[:2]

        await self.storage.update_data(key, {'messages': messages})

        async def task():
            await asyncio.sleep(60)
            await self.storage.update_data(key, {})

        self.timer.update(key, task())

    async def get_answer(self, gpt_settings: database.GPTSettings, key: StorageKey, owner_id: int) -> str | None:
        if gpt_settings.tokens <= 0:
            return

        token = self.credentials.token
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}",
        }

        key = self.get_key(key)
        messages = await self.get_messages(key)

        data = self.data | {
            "completionOptions": {
                "stream": False,
                "temperature": gpt_settings.temperature,
                "maxTokens": f"{min(gpt_settings.max_tokens, max(gpt_settings.tokens, 100))}"
            },
            "messages": [
                {
                    "role": "system",
                    "text": (
                        gpt_settings.promt
                        or _(
                            "DO NOT UNDER ANY CIRCUMSTANCES write your name to the user. "
                            "ALWAYS use English."
                        )
                    )
                },
                *messages
            ]
        }

        async with self.session.post(self.url, headers=headers, json=data) as response:
            data = await response.json()
            if not response.ok:
                logger.warning(f'bad request: {data}')
                return

        assistant_message = data['result']['alternatives'][0]['message']
        messages.append(assistant_message)

        if key.user_id != owner_id:
            gpt_settings.tokens -= int(data['result']['usage']['totalTokens'])
            await gpt_settings.save()

        await self.update_messages(key, messages)

        return assistant_message['text']

    @classmethod
    async def setup(cls, storage: BaseStorage):
        session = aiohttp.ClientSession()
        self = cls(session, storage)

        return self

    async def stop(self):
        await self.session.close()
