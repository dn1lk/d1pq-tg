from datetime import datetime, timedelta, timezone
from random import choice, random

from aiogram import Bot, Router, F, types, enums, flags
from aiogram.fsm.context import FSMContext
from aiogram.utils.chat_action import ChatActionSender
from aiogram.utils.i18n import gettext as _

from core import filters, helpers
from core.middlewares import SQLUpdateMiddleware
from core.utils import database, generation

router = Router(name='other')
router.message.filter(~F.from_user.is_bot, filters.StateFilter(None))

SQLUpdateMiddleware().setup(router)


async def get_gen_kwargs(
        message: types.Message,
        bot: Bot,
        gen_settings: database.GenSettings,
) -> dict:
    async def gen_text() -> dict:
        async with ChatActionSender.typing(chat_id=message.chat.id, bot=bot):
            return {'text': generation.text.get_answer(text, gen_settings)}

    async def gen_sticker() -> dict:
        async with ChatActionSender.choose_sticker(chat_id=message.chat.id, bot=bot):
            return {'sticker': await generation.sticker.get_answer(bot, text, gen_settings)}

    text = helpers.get_text(message)
    return await choice((gen_text, gen_sticker))()


async def chance_filter(message: types.Message) -> bool:
    gen_settings: database.GenSettings = await database.GenSettings.get(chat_id=message.chat.id)

    if datetime.now(tz=timezone(message.date.tzinfo.utcoffset(message.date))) - message.date < timedelta(minutes=5):
        return random() < gen_settings.chance


@router.message(chance_filter, filters.Levenshtein('hello', 'hey', 'здравствуйте', 'привет'))
async def hello_handler(message: types.Message):
    answer = choice(
        (
            _("{user}, hello!"),
            _("Hey, {user}."),
            _("Nice to meet you, {user}."),
            _("My appreciate, {user}."),
            _("Yop, {user}."),
        )
    ).format(user=message.from_user.mention_html())

    await message.answer(answer)


@router.message(F.chat.type == enums.ChatType.PRIVATE)
@router.message(chance_filter)
@router.message(filters.IsMentioned())
@flags.database('gen_settings')
@flags.throttling('gen')
async def gen_answer_handler(
        message: types.Message,
        bot: Bot,
        state: FSMContext,
        gen_settings: database.GenSettings,
):
    answer = await get_gen_kwargs(message, bot, gen_settings)

    if 'text' in answer:
        answer['text'] = helpers.resolve_text(answer['text'])
        message = await message.answer(**answer)
    elif 'sticker' in answer:
        message = await message.answer_sticker(**answer)
    elif 'voice' in answer:
        message = await message.answer_voice(**answer)

    if random() < 0.2:
        await gen_answer_handler(message, bot, state, gen_settings)


@router.message(filters.MagicData(F.event.reply_to_message.from_user.id == F.bot.id))
@flags.database('gen_settings')
@flags.throttling('gen')
async def gen_reply_handler(
        message: types.Message,
        bot: Bot,
        state: FSMContext,
        gen_settings: database.GenSettings,
):
    answer = await get_gen_kwargs(message, bot, gen_settings)

    if 'text' in answer:
        answer['text'] = helpers.resolve_text(answer['text'])
        message = await message.reply(**answer)
    elif 'sticker' in answer:
        message = await message.reply_sticker(**answer)
    elif 'voice' in answer:
        message = await message.reply_voice(**answer)

    if random() < 0.1:
        await gen_answer_handler(message, bot, state, gen_settings)
