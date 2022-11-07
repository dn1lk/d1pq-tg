from random import choice

from aiogram import Bot, types

from .database.context import DataBaseContext


async def gen(message: types.Message, bot: Bot, db: DataBaseContext) -> str:
    stickers = await bot.get_sticker_set(choice(await db.get_data('stickers')))

    if message.text or message.sticker and message.sticker.emoji:
        answer = [
            sticker.file_id for sticker in stickers.stickers
            if sticker.emoji in (message.text or message.sticker.emoji)
        ]
        if answer:
            return choice(answer)

    return choice(stickers.stickers).file_id
