from random import choice
from typing import Optional

from aiogram import Bot, types
from aiogram.dispatcher.fsm.context import FSMContext


async def get(message: types.Message, bot: Bot, state: Optional[FSMContext] = None) -> str:
    stickers = await bot.get_sticker_set(choice(await bot.sql.get_data(message.chat.id, 'stickers', state)))

    if message.text or message.sticker and message.sticker.emoji:
        answer = [
            sticker.file_id for sticker in
            stickers.stickers if sticker.emoji in (message.text or message.sticker.emoji)
        ]
        if answer:
            return choice(answer)

    return choice(stickers.stickers).file_id
