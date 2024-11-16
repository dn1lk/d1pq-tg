import aiohttp
import ydb

import config

from .base import BaseClient


class GPTClient(BaseClient):
    @classmethod
    async def _setup(cls) -> None:
        credentials = ydb.iam.ServiceAccountCredentials.from_file(config.YC_SERVICE_ACCOUNT_FILE_CREDENTIALS)
        cls._session = aiohttp.ClientSession(
            raise_for_status=True,
            base_url="https://llm.api.cloud.yandex.net/",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {credentials.token}",
            },
        )


client = GPTClient()
