import secrets
from datetime import datetime, timedelta, timezone

from aiogram import types

from utils import database


async def gen_chance_filter(message: types.Message) -> bool:
    gen_settings: database.GenSettings = await database.GenSettings.get(chat_id=message.chat.id)

    offset = message.date.tzinfo.utcoffset(message.date)
    if offset and datetime.now(tz=timezone(offset)) - message.date < timedelta(minutes=5):
        return secrets.randbelow(10) / 10 < gen_settings.chance
    return False
