from pathlib import Path

from aiogram.utils.i18n import I18n
from pydantic import BaseSettings, BaseModel, SecretStr


class Bot(BaseModel):
    token: SecretStr
    owner: int


class Settings(BaseSettings):
    bot: Bot
    webhook_url: str
    database_url: str
    port: int = 8080
    google_client: str

    class Config:
        env_nested_delimiter = '__'


CONFIG = Settings()
BASE_DIR = Path(__file__).parent


bot = CONFIG.bot

webhook = CONFIG.webhook_url
sql = CONFIG.database_url
port = CONFIG.port

google = CONFIG.google_client

i18n = I18n(path=BASE_DIR / 'locales', domain='messages')
