from random import choice

from aiogram import Bot

from . import database


async def set_stickers(db: database.SQLContext, sticker: str, chat_id: int, stickers: list[str] = None):
    stickers: list[str] = stickers or (await db.stickers.get(chat_id)) + db.stickers.default

    if sticker not in stickers:
        sticker = [sticker]

        if len(stickers) > 3:
            stickers = stickers[1:] + sticker
            await db.stickers.set(chat_id, stickers)
        else:
            stickers = await db.stickers.cat(chat_id, sticker)
    return stickers


async def gen(bot: Bot, text: str, sticker_set_names: list[str]) -> str:
    async def get_sticker_sets():
        for sticker_set_name in sticker_set_names:
            yield await bot.get_sticker_set(sticker_set_name)

    stickers = sum([sticker_set.stickers async for sticker_set in get_sticker_sets()], [])
    stickers_filtered = [sticker for sticker in stickers if sticker.emoji in text]

    return choice(stickers_filtered or stickers).file_id
