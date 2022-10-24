import asyncio
from random import choice, random

from aiogram import Bot, Router, F, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.base import StorageKey
from aiogram.utils.i18n import gettext as _

from bot.handlers import get_username
from .process import UnoData, UnoUser, get_cards
from .settings import UnoSettings, extract_current_difficulty, extract_current_mode
from .. import Game, keyboards as k

router = Router(name='game:uno:core')


def get_user_ids(entities: list[types.MessageEntity]) -> list[int]:
    return [entity.user.id for entity in entities if entity.user]


async def start_timer(message: types.Message, bot: Bot, state: FSMContext):
    await start_handler(message, bot, state, get_user_ids(message.entities))


async def start_filter(query: types.CallbackQuery):
    user_ids = get_user_ids(query.message.entities)

    if query.from_user.id == user_ids[0]:
        for task in asyncio.all_tasks():
            if task.get_name() == f'game:{query.message.chat.id}':
                task.cancel()
                break

        return {'user_ids': user_ids}


@router.callback_query(k.Games.filter(F.value == 'start'), start_filter)
async def start_handler(
        query: types.CallbackQuery | types.Message,
        bot: Bot,
        state: FSMContext,
        user_ids: list[int],
):
    async def get_uno_users():
        for user_id in user_ids:
            key = StorageKey(
                bot_id=state.key.bot_id,
                chat_id=user_id,
                user_id=user_id,
                destiny=state.key.destiny
            )

            await state.storage.set_state(bot, key, Game.uno)
            await state.storage.update_data(bot, key, {'uno_chat_id': message.chat.id})

            yield user_id, UnoData.pop_from_cards(cards, 7)

    message = query.message if isinstance(query, types.CallbackQuery) else query
    message = await message.delete_reply_markup()

    if random() < 2 / len(user_ids):
        user_ids.append(bot.id)

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
    users = {user_id: UnoUser(cards=cards) async for user_id, cards in get_uno_users()}
    await state.set_state(Game.uno)

    data_uno = UnoData(
        cards=cards,
        users=users,
        current_index=choice(range(len(users))),
        settings=UnoSettings(difficulty=extract_current_difficulty(message), mode=extract_current_mode(message)),
    )

    from .process.core import post

    await post(message, data_uno, state, _("So, <b>let's start the game.</b>"))


@router.callback_query(k.Games.filter(F.value == 'start'))
async def start_no_owner_handler(query: types.CallbackQuery):
    await query.answer(_("Only {user} can start the game.").format(user=query.message.entities[3].user.first_name))


@router.callback_query(k.Games.filter(F.value == 'join'))
async def join_handler(query: types.CallbackQuery):
    user_ids = get_user_ids(query.message.entities)

    if query.from_user.id in user_ids:
        await query.answer(_("You are already in the list!"))
    elif len(user_ids) == 10:
        await query.answer(_("The number of players is already 10 people.\nI can't write anymore."))
    else:
        await query.message.edit_text(
            f'{query.message.html_text}\n{get_username(query.from_user)}',
            reply_markup=query.message.reply_markup
        )

        await query.answer(_("Now there are one more players!"))


@router.callback_query(k.Games.filter(F.value == 'leave'))
async def leave_handler(query: types.CallbackQuery):
    user_ids = get_user_ids(query.message.entities)

    if query.from_user.id in user_ids:
        if len(user_ids) == 1:
            for task in asyncio.all_tasks():
                if task.get_name() == f'game:{query.message.chat.id}':
                    task.cancel()
                    break

            await query.message.edit_text(
                choice(
                    (
                        _("Nobody wants to play =(."),
                        _("And who is there to play with?"),
                    )
                )
            )
        else:
            html_text = query.message.html_text

            await query.message.edit_text(
                html_text.replace(f'\n{get_username(query.from_user)}', ''),
                reply_markup=query.message.reply_markup
            )

            await query.answer(_("Now there is one less player!"))
    else:
        await query.answer(_("You are not in the list yet!"))
