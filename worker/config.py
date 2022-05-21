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
    google_client: str


CONFIG = Settings(_env_nested_delimiter='__')
BASE_DIR = Path(__file__).parent

bot = CONFIG.bot
webhook = CONFIG.webhook_url
sql = CONFIG.database_url
google = CONFIG.google_client

i18n = I18n(path=BASE_DIR / 'locales', domain='messages')
