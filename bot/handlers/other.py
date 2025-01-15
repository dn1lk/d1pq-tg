import secrets

from aiogram import Bot, F, Router, enums, flags, types
from aiogram.fsm.context import FSMContext
from aiogram.utils import formatting
from aiogram.utils.i18n import I18n
from aiogram.utils.i18n import gettext as _

from core import filters
from core.middlewares import SQLUpdateMiddleware
from utils import database, generation

from .misc.filters import gen_chance_filter
from .misc.helpers import get_gen_kwargs

ANSWER_CHANCE = 0.1
REPLY_CHANCE = 0.2

router = Router(name="other")
router.message.filter(~F.from_user.is_bot, filters.StateFilter(None))

SQLUpdateMiddleware().setup(router)


@router.message(gen_chance_filter, filters.Levenshtein("hello", "hey", "здравствуйте", "привет"))
async def hello_handler(message: types.Message) -> None:
    assert message.from_user is not None, "wrong user"

    _user = formatting.TextMention(message.from_user.first_name, user=message.from_user)
    content = formatting.Text(
        *secrets.choice(
            (
                (_user, ", ", _("hello!")),
                (_("Hey"), ", ", _user, "."),
                (_("Nice to meet you", ", ", _user, ".")),
                (_("My appreciate", ", ", _user, ".")),
                (_("Yop", ", ", _user, ".")),
            ),
        ),
    )

    await message.answer(**content.as_kwargs())


@router.message(F.chat.type == enums.ChatType.PRIVATE)
@router.message(gen_chance_filter)
@router.message(filters.IsMentioned())
@flags.database(("gen_settings", "gpt_settings"))
@flags.throttling("gen")
async def gen_answer_handler(
    message: types.Message,
    bot: Bot,
    owner_id: int,
    state: FSMContext,
    i18n: I18n,
    gen_settings: database.GenSettings,
    gpt_settings: database.GPTSettings,
    gpt: generation.YandexGPT,
) -> None:
    gen_kwargs = await get_gen_kwargs(
        message,
        bot,
        owner_id,
        state,
        i18n,
        gen_settings,
        gpt_settings,
        gpt,
    )

    if "text" in gen_kwargs:
        message = await message.answer(**gen_kwargs)
    elif "sticker" in gen_kwargs:
        message = await message.answer_sticker(**gen_kwargs)
    elif "voice" in gen_kwargs:
        message = await message.answer_voice(**gen_kwargs)

    if secrets.randbelow(10) / 10 < ANSWER_CHANCE:
        key = gpt.prepare_key(state.key)

        messages = await gpt.get_messages(key)
        messages.append(
            {
                "role": "system",
                "text": _(
                    "Continuing with the previous sentence.",
                ),
            },
        )

        await gpt.update_messages(key, messages)
        await gen_answer_handler(message, bot, owner_id, state, i18n, gen_settings, gpt_settings, gpt)


@router.message(filters.MagicData(F.event.reply_to_message.from_user.id == F.bot.id))
@flags.database(("gen_settings", "gpt_settings"))
@flags.throttling("gen")
async def gen_reply_handler(
    message: types.Message,
    bot: Bot,
    owner_id: int,
    state: FSMContext,
    i18n: I18n,
    gen_settings: database.GenSettings,
    gpt_settings: database.GPTSettings,
    gpt: generation.YandexGPT,
) -> None:
    gen_kwargs = await get_gen_kwargs(
        message,
        bot,
        owner_id,
        state,
        i18n,
        gen_settings,
        gpt_settings,
        gpt,
    )

    if "text" in gen_kwargs:
        message = await message.reply(**gen_kwargs)
    elif "sticker" in gen_kwargs:
        message = await message.reply_sticker(**gen_kwargs)
    elif "voice" in gen_kwargs:
        message = await message.reply_voice(**gen_kwargs)

    if secrets.randbelow(10) / 10 < REPLY_CHANCE:
        key = gpt.prepare_key(state.key)

        messages = await gpt.get_messages(key)
        messages.append(
            {
                "role": "system",
                "text": _(
                    "Continuing with the previous sentence.",
                ),
            },
        )

        await gpt.update_messages(key, messages)
        await gen_answer_handler(message, bot, owner_id, state, i18n, gen_settings, gpt_settings, gpt)
