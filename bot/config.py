from pathlib import Path

from aiogram.utils.i18n import I18n
from pydantic import BaseSettings, SecretStr


class Bot(BaseSettings):
    token: SecretStr
    owner: int

    class Config:
        env_prefix = 'BOT_M_'


class Provider(BaseSettings):
    domain_url: str | None = None
    host: str = '0.0.0.0'
    port: int = 8080

    database_url: str


bot = Bot()
provider = Provider()

i18n = I18n(path=Path.cwd() / 'bot' / 'locales', domain='messages')
