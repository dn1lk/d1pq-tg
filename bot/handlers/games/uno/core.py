from random import choice, random, choices
from typing import List

from aiogram import Router, F, types, Bot
from aiogram.dispatcher.fsm.context import FSMContext
from aiogram.utils.i18n import gettext as _

from bot import keyboards as k
from . import UnoManager, get_sticker
from .bot import gen
from .. import Game
from ... import get_username

router = Router(name='game:uno:core')


@router.callback_query(k.GamesData.filter(F.value == 'start'))
async def game_uno_start(query: types.CallbackQuery, bot: Bot, state: FSMContext):
    data = await state.get_data()
    users: List[int] = data.get('uno', [])

    if bot.id not in users and random() <= 2 / await bot.get_chat_member_count(query.message.chat.id):
        bot_user = await bot.get_me()
        users.append(bot.id)
        await query.message.edit_text(
            query.message.html_text + '\n' + get_username(bot_user),
            reply_markup=query.message.reply_markup
        )
        await query.message.answer(
            choice(
                (
                    _("Да-да, я тоже играю!"),
                    _("Поиграю с вами."),
                    _("А в игре и я тоже!")
                )
            )
        )

    if len(users) > 1:
        await query.message.delete_reply_markup()

        cards = (await bot.get_sticker_set('uno_cards')).stickers
        data_users = {user_id: [get_sticker(card) for card in choices(cards, k=6)] for user_id in users}
        data_now_user = (await bot.get_chat_member(query.message.chat.id, choice(tuple(data_users)))).user

        data_uno = UnoManager(users=data_users, now_user=data_now_user)

        if data_uno.now_user.id == bot.id:
            data_uno = await gen(query.message, bot, state, data, data_uno)
            answer = _("Какая неожиданность, мой ход.")
        else:
            answer = _("{user}, твой ход.").format(user=get_username(data_uno.now_user))

        await state.set_state(Game.uno)
        await query.message.answer(_("<b>Итак, начнём игру.</b>\n\n") + answer, reply_markup=k.game_uno_show_cards())

        await state.update_data(uno=data_uno)
    else:
        await query.answer(_("А с кем играть то? =)"))


@router.callback_query(k.GamesData.filter(F.value == 'join'))
async def game_uno_join(query: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    users = data.get('uno', [])

    if query.from_user.id in users:
        await query.answer(_("Ты уже участвуешь!"))
    else:
        await query.message.edit_text(
            query.message.html_text + '\n' + get_username(query.from_user),
            reply_markup=query.message.reply_markup
        )

        await query.answer(_("Теперь участников стало на один больше!"))

        users.append(query.from_user.id)
        await state.update_data(uno=users)


@router.callback_query(k.GamesData.filter(F.value == 'decline'))
async def game_uno_decline(query: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    users: List[int] = data.get('uno', [])

    if query.from_user.id in users:
        users.remove(query.from_user.id)

        await query.message.edit_text(
            query.message.html_text.replace(
                "\n" + get_username(query.from_user),
                '',
            ),
            reply_markup=query.message.reply_markup
        )

        await query.answer(_("Теперь участников стало на один меньше!"))
        await state.update_data(uno=users)
    else:
        await query.answer(_("Ты ещё не участвуешь!"))
