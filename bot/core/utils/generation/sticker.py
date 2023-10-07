from random import choice

from aiogram import Bot

from core.utils import database


async def gen(
        bot: Bot,
        text: str,
        gen_settings: database.GenSettings
) -> str | None:
    stickers = []
    stickers_filtered = []
    for sticker_set_name in (database.DEFAULT_STICKER_SET, *(gen_settings.stickers or [])):
        for sticker in (await bot.get_sticker_set(sticker_set_name)).stickers:
            stickers.append(sticker)

            if sticker.emoji in text:
                stickers_filtered.append(sticker)

    return choice(stickers_filtered or stickers).file_id
