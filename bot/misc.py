import os

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.redis import RedisStorage, DefaultKeyBuilder
from aiogram.fsm.strategy import FSMStrategy
from aiogram.utils.i18n import I18n

import config

BASE_DIR = os.curdir

bot = Bot(
    token=config.BOT_TOKEN,
    parse_mode="HTML"
)

if config.REDIS_USE:
    storage = RedisStorage.from_url(
        config.REDIS_URL,
        key_builder=DefaultKeyBuilder(with_destiny=True),
        data_ttl=60 * 60 * 24,  # one day
    )
else:
    storage = None

dp = Dispatcher(
    name='dispatcher',
    storage=storage,
    fsm_strategy=FSMStrategy.CHAT,
    owner_id=config.BOT_OWNER_ID,
)

i18n = I18n(path=f'{BASE_DIR}/core/locales', domain='messages')
