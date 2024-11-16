import secrets

from aiogram import Bot, types

from utils import database


async def get_answer(bot: Bot, text: str, gen_settings: database.GenSettings) -> str:
    stickers: list[types.Sticker] = []
    stickers_filtered: list[types.Sticker] = []
    for sticker_set_name in (database.DEFAULT_STICKER_SET, *(gen_settings.stickers or [])):
        for sticker in (await bot.get_sticker_set(sticker_set_name)).stickers:
            stickers.append(sticker)

            if sticker.emoji and sticker.emoji in text:
                stickers_filtered.append(sticker)

    return secrets.choice(stickers_filtered or stickers).file_id
