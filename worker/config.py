from pathlib import Path

from aiogram.utils.i18n import I18n
from pydantic import BaseSettings, SecretStr


class Bot(BaseSettings):
    token: SecretStr
    owner: int

    class Config:
        env_prefix = 'BOT_'


class Heroku(BaseSettings):
    domain_url: str
    database_url: str
    host: str = '0.0.0.0'
    port: int = 8080


class Google(BaseSettings):
    google_client: str


BASE_DIR = Path(__file__).parent

bot = Bot()
heroku = Heroku()
google = Google()

i18n = I18n(path=BASE_DIR / 'locales', domain='messages')
