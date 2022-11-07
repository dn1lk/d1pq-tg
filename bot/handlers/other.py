from datetime import datetime, timedelta
from random import choice, random

from aiogram import Router, Bot, F, types, filters, flags
from aiogram.utils.chat_action import ChatActionSender
from aiogram.utils.i18n import I18n, gettext as _

from bot import filters as f
from bot.utils import balaboba, markov, voice, sticker
from bot.utils.database.context import DataBaseContext
from . import get_username

router = Router(name='message')
router.message.filter(~F.from_user.is_bot, F.text, filters.StateFilter(None))


def answer_check(answer: str) -> str:
    answer = answer.strip()
    answer = answer[0].upper() + answer[1:]

    if answer[-1] not in '!?:.()>':
        answer += '.'

    return answer


async def get_gen_args(
        message: types.Message,
        bot: Bot,
        i18n: I18n,
        db: DataBaseContext,
        yalm: balaboba.Yalm,
        messages: list[str],
) -> dict:
    async def gen_markov() -> dict:
        async with ChatActionSender.typing(chat_id=message.chat.id):
            accuracy: int | None = await db.get_data('accuracy')

            return {
                'text': markov.gen(
                    locale=i18n.current_locale,
                    messages=messages,
                    text=message.text,
                    state_size=accuracy,
                )
            }

    async def gen_voice() -> dict:  # now working :(
        async with ChatActionSender.record_voice(chat_id=message.chat.id):
            answer = await gen_markov()
            return await voice.gen(answer=answer['text'], locale=i18n.current_locale)

    async def gen_balaboba() -> dict:
        async with ChatActionSender.typing(chat_id=message.chat.id):
            return {
                'text': await yalm.gen(
                    i18n.current_locale,
                    message.text,
                    choice(yalm.intros['ru'])
                )
            }

    async def gen_sticker() -> dict:
        async with ChatActionSender.choose_sticker(chat_id=message.chat.id, interval=1):
            return {'sticker': await sticker.gen(message, bot, db)}

    return await choice([gen_markov, gen_sticker, gen_balaboba])()


@router.message(filters.MagicData(F.event.reply_to_message.from_user.id == F.bot.id))
@flags.throttling('gen')
async def gen_reply_handler(
        message: types.Message,
        bot: Bot,
        i18n: I18n,
        db: DataBaseContext,
        yalm: balaboba.Yalm,
        messages: list[str],
):
    answer = await get_gen_args(message, bot, i18n, db, yalm, messages)

    if 'text' in answer:
        answer['text'] = answer_check(answer['text'])
        await message.reply(**answer)
    elif 'sticker' in answer:
        await message.reply_sticker(**answer)
    elif 'voice' in answer:
        await message.reply_voice(**answer)


async def chance_filter(message: types.Message, bot: Bot, db: DataBaseContext) -> bool:
    if datetime.now(tz=message.date.tzinfo) - message.date < timedelta(minutes=5):
        chance: float = await db.get_data('chance')

        return random() < (chance / await bot.get_chat_member_count(message.chat.id))


@router.message(chance_filter, f.LevenshteinFilter(lev={'hello', 'hey', 'здравствуйте', 'привет'}))
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
        ).format(user=get_username(message.from_user))
    )


@router.message(F.chat.type == 'private')
@router.message(chance_filter)
@router.message(f.LevenshteinFilter(lev={'delete', 'делите'}))
@flags.throttling('gen')
async def gen_answer_handler(
        message: types.Message,
        bot: Bot,
        i18n: I18n,
        db: DataBaseContext,
        yalm: balaboba.Yalm,
        messages: list[str],
):
    answer = await get_gen_args(message, bot, i18n, db, yalm, messages)

    if 'text' in answer:
        answer['text'] = answer_check(answer['text'])
        await message.answer(**answer)
    elif 'sticker' in answer:
        await message.answer_sticker(**answer)
    elif 'voice' in answer:
        await message.answer_voice(**answer)
