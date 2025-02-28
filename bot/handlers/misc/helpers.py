import secrets
from typing import Any

from aiogram import Bot, types
from aiogram.fsm.context import FSMContext
from aiogram.utils.chat_action import ChatActionSender
from aiogram.utils.i18n import I18n

from core import helpers
from utils import database, generation


async def get_gen_kwargs(
    message: types.Message,
    bot: Bot,
    owner_id: int,
    state: FSMContext,
    i18n: I18n,
    gen_settings: database.GenSettings,
    gpt_settings: database.GPTSettings,
    gpt: generation.YandexGPT,
) -> dict[str, Any]:
    async def gen_text() -> dict[str, str]:
        async with ChatActionSender.typing(chat_id=message.chat.id, bot=bot):
            answer = await gpt.get_answer(gpt_settings, state.key, owner_id)
            if answer is None:
                answer = generation.text.get_answer(text, i18n, gen_settings)

            answer = helpers.resolve_text(answer, escape=True)
            return {"text": answer}

    async def gen_sticker() -> dict[str, str]:
        async with ChatActionSender.choose_sticker(chat_id=message.chat.id, bot=bot):
            return {"sticker": await generation.sticker.get_answer(bot, text, gen_settings)}

    text = helpers.get_text(message)
    return await secrets.choice((*(gen_text,) * 5, gen_sticker))()
