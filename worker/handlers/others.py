from datetime import datetime, timedelta
from random import choice, random
from typing import Optional

from aiogram import Router, Bot, F, types, filters, flags
from aiogram.dispatcher.fsm.context import FSMContext
from aiogram.utils.chat_action import ChatActionSender
from aiogram.utils.i18n import I18n

from worker import filters as f
from worker.utils import (aiobalaboba, markov, voice, sticker)

router = Router(name='message')


async def get_gen_args(
        message: types.Message,
        bot: Bot,
        i18n: I18n,
        state: FSMContext,
        messages: Optional[list] = None) -> dict:
    async def gen_markov() -> dict:
        async with ChatActionSender.typing(chat_id=message.chat.id):
            accuracy: Optional[int] = await bot.sql.get_data(message.chat.id, 'accuracy', state)

            return {
                'text': await markov.get(
                    messages=messages,
                    text=message.text,
                    state_size=accuracy
                )
            }

    async def gen_voice() -> dict:  # now working :(
        async with ChatActionSender.record_voice(chat_id=message.chat.id):
            return await voice.get((await gen_markov())['text'], i18n.current_locale)

    async def gen_balaboba() -> dict:  # not working too :(
        async with ChatActionSender.typing(chat_id=message.chat.id):
            return {'text': await aiobalaboba.get(message.text, choice([4, 3, 5, 7, 11]))}

    async def gen_sticker() -> dict:
        async with ChatActionSender.choose_sticker(chat_id=message.chat.id, interval=1):
            return {'sticker': await sticker.get(message, bot, state)}

    return await choice([gen_markov, gen_sticker])()


@router.message(~F.from_user.is_bot, filters.MagicData(magic_data=F.event.reply_to_message.from_user.id == F.bot.id))
async def gen_reply_handler(
        message: types.Message,
        bot: Bot,
        i18n: I18n,
        state: Optional[FSMContext] = None,
        messages: Optional[list] = None, ):
    answer = await get_gen_args(message, bot, i18n, state, messages)

    if answer.get('text'):
        await message.reply(**answer)
    elif answer.get('sticker'):
        await message.reply_sticker(**answer)
    elif answer.get('voice'):
        await message.reply_voice(**answer)


async def gen_chance_filter(message: types.Message, bot: Bot, state: Optional[FSMContext] = None) -> bool:
    if not message.left_chat_member:
        if datetime.now(tz=message.date.tzinfo) - message.date < timedelta(minutes=5):
            chance: Optional[float] = await bot.sql.get_data(message.chat.id, 'chance', state)

            return random() < (chance / await bot.get_chat_member_count(message.chat.id))


@router.message(F.chat.type == 'private')
@router.message(~F.from_user.is_bot, f.LevenshteinFilter(lev=('delete', 'делите')))
@router.message(~F.from_user.is_bot, gen_chance_filter)
@flags.data('messages')
@flags.gen
@flags.chat_action("typing")
async def gen_answer_handler(
        message: types.Message,
        bot: Bot,
        i18n: I18n,
        state: Optional[FSMContext] = None,
        messages: Optional[list] = None,
):
    answer = await get_gen_args(message, bot, i18n, state, messages)

    if answer.get('text'):
        await message.answer(**answer)
    elif answer.get('sticker'):
        await message.answer_sticker(**answer)
    elif answer.get('voice'):
        await message.answer_voice(**answer)
