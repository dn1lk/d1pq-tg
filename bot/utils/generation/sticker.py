import secrets

from aiogram import Bot, types

from utils import database


async def get_answer(
    bot: Bot,
    text: str,
    gen_settings: database.models.GenSettings,
) -> str:
    saved_stickers = gen_settings.stickers if gen_settings.with_stickers else []

    stickers: list[types.Sticker] = []
    stickers_filtered: list[types.Sticker] = []
    for sticker_set_name in (database.models.DEFAULT_STICKER_SET, *saved_stickers):
        sticker_set = await bot.get_sticker_set(sticker_set_name)

        for sticker in sticker_set.stickers:
            stickers.append(sticker)

            if sticker.emoji and sticker.emoji in text:
                stickers_filtered.append(sticker)

    return secrets.choice(stickers_filtered or stickers).file_id
