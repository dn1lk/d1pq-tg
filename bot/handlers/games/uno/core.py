import asyncio
from random import choice, random, choices

from aiogram import Bot, Router, F, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.base import StorageKey
from aiogram.utils.i18n import gettext as _

from bot.handlers import get_username
from . import uno_timeout
from .bot import UnoBot
from .cards import get_cards
from .data import UnoData
from .. import Game, timer, keyboards as k

router = Router(name='game:uno:core')


def get_user_ids(entities: list[types.MessageEntity]) -> set[int]:
    return {entity.user.id for entity in entities if entity.user}


async def start_filter(query: types.CallbackQuery):
    user_ids = get_user_ids(query.message.entities)

    if user_ids:
        for task in asyncio.all_tasks():
            if task.get_name() == 'game' + ':' + str(query.message.chat.id):
                task.cancel()
                break

        return {'user_ids': user_ids}


async def start_timer_handler(
        message: types.Message,
        bot: Bot,
        state: FSMContext,
):
    user_ids = get_user_ids(message.entities)

    if user_ids:
        await start_handler(message, bot, state, user_ids)
    else:
        await start_no_users_handler(await message.edit_reply_markup(k.uno_start()))


@router.callback_query(
    k.Games.filter(F.value == 'start'),
    F.from_user.id == F.message.entities[1].user.id,
    start_filter
)
async def start_handler(
        query: types.CallbackQuery | types.Message,
        bot: Bot,
        state: FSMContext,
        user_ids: set[int],
):
    async def get_users_with_cards():
        for user_id in user_ids:
            key = StorageKey(
                bot_id=state.key.bot_id,
                chat_id=user_id,
                user_id=user_id,
                destiny=state.key.destiny
            )

            await state.storage.set_state(bot, key, Game.uno)
            await state.storage.update_data(bot, key, {'uno_chat_id': message.chat.id})

            yield user_id, choices(cards, k=6)

    message = query.message if isinstance(query, types.CallbackQuery) else query
    message = await message.delete_reply_markup()

    if random() < 2 / len(user_ids):
        user_ids.add(bot.id)

        await message.edit_text(message.html_text + '\n' + get_username(await bot.get_me()))
        await message.answer(
            choice(
                (
                    _("Yes, I play too!"),
                    _("I'll play with you."),
                    _("I'm with you.")
                )
            )
        )

    cards = await get_cards(bot)
    users = {user: cards async for user, cards in get_users_with_cards()}

    current_user_id = choice(tuple(users))
    data_uno = UnoData(
        users=users,
        current_user_id=current_user_id,
    )

    await state.set_state(Game.uno)
    await state.update_data(uno=data_uno.dict())

    answer = _("So, <b>let's start the game.</b>") + "\n\n"

    if data_uno.current_user_id == bot.id:
        message = await message.reply(answer + _("What a surprise, my turn."))
        bot_uno = UnoBot(message=message, bot=bot, data=data_uno)

        await bot_uno.gen(state, bot_uno.get_cards())
    else:
        user = (await bot.get_chat_member(message.chat.id, current_user_id)).user
        message = await message.reply(
            answer + _("{user}, your turn.").format(user=get_username(user)),
            reply_markup=k.uno_show_cards(),
        )

        timer(state, uno_timeout, message=message)


@router.callback_query(k.Games.filter(F.value == 'start'), F.from_user.id == F.message.entities[1].user.id)
async def start_no_users_handler(query: types.CallbackQuery | types.Message):
    await query.answer(_("And who is there to play with?"))


@router.callback_query(k.Games.filter(F.value == 'start'))
async def start_no_owner_handler(query: types.CallbackQuery):
    await query.answer(_("You cannot start this game."))


@router.callback_query(k.Games.filter(F.value == 'join'))
async def join_handler(query: types.CallbackQuery):
    users = {entity.user.id for entity in query.message.entities[3:] if entity.user}

    if query.from_user.id in users:
        await query.answer(_("You are already in the list!"))
    else:
        html_text = query.message.html_text

        if not users:
            html_text = html_text.replace(
                get_username(query.message.entities[1].user),
                get_username(query.from_user)
            )

        await query.message.edit_text(
            html_text + '\n' + get_username(query.from_user),
            reply_markup=query.message.reply_markup
        )

        await query.answer(_("Now there are one more players!"))


@router.callback_query(k.Games.filter(F.value == 'leave'))
async def leave_handler(query: types.CallbackQuery):
    users = {entity.user.id for entity in query.message.entities[3:] if entity.user}

    if query.from_user.id in users:
        await query.message.edit_text(
            query.message.html_text.replace("\n" + get_username(query.from_user), ""),
            reply_markup=query.message.reply_markup
        )

        await query.answer(_("Now there is one less player!"))
    else:
        await query.answer(_("You are not in the list yet!"))
