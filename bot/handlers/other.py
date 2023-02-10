from datetime import datetime, timedelta
from random import choice, random

from aiogram import Bot, Router, F, types, flags
from aiogram.utils.chat_action import ChatActionSender
from aiogram.utils.i18n import I18n, gettext as _

from . import answer_check
from .. import filters
from ..utils import markov, sticker, database

router = Router(name='message')
router.message.filter(~F.from_user.is_bot, filters.StateFilter(None))


async def get_gen_args(
        message: types.Message,
        bot: Bot,
        db: database.SQLContext,
        i18n: I18n,
) -> dict:
    async def gen_markov() -> dict:
        async with ChatActionSender.typing(chat_id=message.chat.id):
            accuracy: int = await db.accuracy.get(message.chat.id)
            messages: list[str] | None = await db.messages.get(message.chat.id)

            return {'text': markov.gen(i18n.current_locale, text, messages, state_size=accuracy)}

    async def gen_sticker() -> dict:
        async with ChatActionSender.choose_sticker(chat_id=message.chat.id):
            stickers: list[str] = await db.stickers.get(message.chat.id)
            return {'sticker': await sticker.gen(bot, text, stickers)}

    text = message.text or message.caption or (message.poll.question if message.poll else "")
    return await choice((gen_markov, gen_sticker))()


async def chance_filter(message: types.Message, db: database.SQLContext) -> bool:
    if datetime.now(tz=message.date.tzinfo) - message.date < timedelta(minutes=5):
        return random() < await db.chance.get(message.chat.id)


@router.message(chance_filter, filters.LevenshteinFilter('hello', 'hey', 'здравствуйте', 'привет'))
async def hello_handler(message: types.Message):
    await message.answer(
        choice(
            (
                _("{user}, hello!"),
                _("Hey, {user}."),
                _("Nice to meet you, {user}."),
                _("My appreciate, {user}."),
                _("Yop, {user}"),
            )
        ).format(user=message.from_user)
    )


@router.message(F.chat.type == 'private')
@router.message(chance_filter)
@router.message(filters.LevenshteinFilter('delete', 'делите'))
@flags.throttling('gen')
async def gen_answer_handler(
        message: types.Message,
        bot: Bot,
        db: database.SQLContext,
        i18n: I18n,
):
    answer = await get_gen_args(message, bot, db, i18n)

    if 'text' in answer:
        answer['text'] = answer_check(answer['text'])
        message = await message.answer(**answer)
    elif 'sticker' in answer:
        message = await message.answer_sticker(**answer)
    elif 'voice' in answer:
        message = await message.answer_voice(**answer)

    if random() < 0.2:
        await gen_answer_handler(message, bot, db, i18n)


@router.message(filters.MagicData(F.event.reply_to_message.from_user.id == F.bot.id))
@flags.throttling('gen')
async def gen_reply_handler(
        message: types.Message,
        bot: Bot,
        db: database.SQLContext,
        i18n: I18n,
):
    answer = await get_gen_args(message, bot, db, i18n)

    if 'text' in answer:
        answer['text'] = answer_check(answer['text'])
        message = await message.reply(**answer)
    elif 'sticker' in answer:
        message = await message.reply_sticker(**answer)
    elif 'voice' in answer:
        message = await message.reply_voice(**answer)

    if random() < 0.1:
        await gen_answer_handler(message, bot, db, i18n)
