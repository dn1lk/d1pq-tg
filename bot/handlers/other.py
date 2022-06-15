from datetime import datetime, timedelta
from random import choice, random

from aiogram import Router, Bot, F, types, flags
from aiogram.utils.chat_action import ChatActionSender
from aiogram.utils.i18n import I18n

from bot import filters as f
from bot.utils import (balaboba, markov, voice, sticker)
from bot.utils.database.context import DataBaseContext

router = Router(name='message')
router.message.filter(~F.from_user.is_bot)


async def get_gen_args(
        message: types.Message,
        bot: Bot,
        i18n: I18n,
        db: DataBaseContext,
        messages: list | None = None,
) -> dict:
    async def gen_markov() -> dict:
        async with ChatActionSender.typing(chat_id=message.chat.id):
            accuracy: int | None = await db.get_data('accuracy')

            return {
                'text': await markov.gen(locale=i18n.current_locale, messages=messages, text=message.text,
                                         state_size=accuracy)
            }

    async def gen_voice() -> dict:  # now working :(
        async with ChatActionSender.record_voice(chat_id=message.chat.id):
            return await voice.gen(answer=(await gen_markov())['text'], locale=i18n.current_locale)

    async def gen_balaboba() -> dict:  # not working too :(
        async with ChatActionSender.typing(chat_id=message.chat.id):
            return {'text': await balaboba.gen(i18n.current_locale, message.text, choice([4, 3, 5, 7, 11]))}

    async def gen_sticker() -> dict:
        async with ChatActionSender.choose_sticker(chat_id=message.chat.id, interval=1):
            return {'sticker': await sticker.gen(message, bot, db)}

    return await choice([gen_markov, gen_sticker])()


@router.message(magic_data=F.reply_to_message.from_user.id == F.bot.id)
@flags.throttling('gen')
@flags.data('messages')
@flags.gen
@flags.chat_action("typing")
async def gen_reply_handler(
        message: types.Message,
        bot: Bot,
        i18n: I18n,
        db: DataBaseContext,
        messages: list | None = None,
):
    answer = await get_gen_args(message, bot, i18n, db, messages)

    if answer.get('text'):
        await message.reply(**answer)
    elif answer.get('sticker'):
        await message.reply_sticker(**answer)
    elif answer.get('voice'):
        await message.reply_voice(**answer)


async def gen_chance_filter(message: types.Message, bot: Bot, db: DataBaseContext) -> bool:
    if not message.left_chat_member:
        if datetime.now(tz=message.date.tzinfo) - message.date < timedelta(minutes=5):
            chance: float | None = await db.get_data('chance')

            return random() < (chance / await bot.get_chat_member_count(message.chat.id))


@router.message(F.chat.type == 'private')
@router.message(f.LevenshteinFilter(lev=('delete', 'делите')))
@router.message(gen_chance_filter)
@flags.throttling('gen')
@flags.data('messages')
@flags.gen
@flags.chat_action("typing")
async def gen_answer_handler(
        message: types.Message,
        bot: Bot,
        i18n: I18n,
        db: DataBaseContext,
        messages: list | None = None,
):
    answer = await get_gen_args(message, bot, i18n, db, messages)

    if answer.get('text'):
        await message.answer(**answer)
    elif answer.get('sticker'):
        await message.answer_sticker(**answer)
    elif answer.get('voice'):
        await message.answer_voice(**answer)
