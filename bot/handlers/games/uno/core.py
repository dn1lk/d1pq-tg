import asyncio
from random import choice, random, choices

from aiogram import Bot, Router, F, types
from aiogram.dispatcher.fsm.context import FSMContext
from aiogram.dispatcher.fsm.storage.base import StorageKey
from aiogram.utils.i18n import gettext as _

from bot.handlers import get_username
from . import uno_timeout
from .bot import UnoBot
from .cards import get_cards
from .data import UnoData
from .. import Game, timer, keyboards as k

router = Router(name='game:uno:core')


async def start_filter(query: types.CallbackQuery):
    users_id = {entity.user.id for entity in query.message.entities[3:] if entity.user}

    if users_id:
        for task in asyncio.all_tasks():
            if task.get_name() == 'game' + ':' + str(query.message.chat.id):
                task.cancel()
                break

        return {'users_id': users_id}


@router.callback_query(
    k.Games.filter(F.value == 'start'),
    F.from_user.id == F.message.entities[1].user.id,
    start_filter
)
async def start_handler(
        query: types.CallbackQuery | types.Message,
        bot: Bot,
        state: FSMContext,
        users_id: set | None = None
):
    message = query.message if isinstance(query, types.CallbackQuery) else query
    message = await message.delete_reply_markup()

    if not users_id:
        users_id = {entity.user.id for entity in message.entities[3:] if entity.user}

        if not users_id:
            return await start_no_users_handler(await message.edit_reply_markup(k.uno_start()))

    if random() < 2 / len(users_id):
        users_id.add(bot.id)

        await message.edit_text(
            message.html_text + '\n' + get_username(await bot.get_me()),
            reply_markup=message.reply_markup
        )
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
    users = {}

    for user_id in users_id:
        users[user_id] = choices(cards, k=6)
        key = StorageKey(
            bot_id=state.key.bot_id,
            chat_id=user_id,
            user_id=user_id,
            destiny=state.key.destiny
        )

        await state.storage.set_state(bot, key, Game.uno)
        await state.storage.update_data(bot, key, {'uno_chat_id': message.chat.id})

    member = await bot.get_chat_member(message.chat.id, choice(tuple(users_id)))
    data_uno = UnoData(
        users=users,
        next_user_id=member.user.id,
    )

    await state.set_state(Game.uno)

    answer = _("So, <b>let's start the game.</b>") + "\n\n"

    if data_uno.next_user_id == bot.id:
        message = await message.reply(answer + _("What a surprise, my move."))
        bot_uno = UnoBot(message=message, bot=bot, data=data_uno)

        await bot_uno.gen(state, bot_uno.get_cards())
    else:
        message = await message.reply(
            answer + _("{user}, your move.").format(user=get_username(await data_uno.get_user(bot, message.chat.id))),
            reply_markup=k.uno_show_cards(),
        )

        await state.update_data(uno=data_uno.dict())
        timer(state, uno_timeout, message=message, data_uno=data_uno)


@router.callback_query(k.Games.filter(F.value == 'start'), F.from_user.id == F.message.entities[1].user.id)
async def start_no_users_handler(query: types.CallbackQuery | types.Message):
    await query.answer(_("And who do you play with? =)."))


@router.callback_query(k.Games.filter(F.value == 'start'))
async def start_no_owner_handler(query: types.CallbackQuery):
    await query.answer(_("You cannot start this game."))


@router.callback_query(k.Games.filter(F.value == 'join'))
async def game_uno_join(query: types.CallbackQuery):
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
async def game_uno_leave(query: types.CallbackQuery):
    users = {entity.user.id for entity in query.message.entities[3:] if entity.user}

    if query.from_user.id in users:
        await query.message.edit_text(
            query.message.html_text.replace("\n" + get_username(query.from_user), ""),
            reply_markup=query.message.reply_markup
        )

        await query.answer(_("Now there is one less player!"))
    else:
        await query.answer(_("You are not in the list yet!"))
