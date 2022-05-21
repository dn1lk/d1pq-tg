from pathlib import Path

from aiogram.utils.i18n import I18n
from pydantic import BaseSettings, BaseModel, SecretStr


class Bot(BaseModel):
    token: SecretStr
    owner: int


class Heroku(BaseModel):
    domain_url: str
    database_url: str
    host: str = '0.0.0.0'
    port: int = 8080


class Settings(BaseSettings):
    bot: Bot
    heroku: Heroku
    google_client: str

    class Config:
        env_nested_delimiter = '__'


CONFIG = Settings()
BASE_DIR = Path(__file__).parent


bot = CONFIG.bot
heroku = CONFIG.heroku
google = CONFIG.google_client

i18n = I18n(path=BASE_DIR / 'locales', domain='messages')
