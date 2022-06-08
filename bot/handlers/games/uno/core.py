from random import choice, random, choices
from typing import List

from aiogram import Router, F, types, Bot
from aiogram.dispatcher.fsm.context import FSMContext
from aiogram.utils.i18n import gettext as _

from bot.handlers import get_username

from bot import keyboards as k

from .manager import UnoManager
from .action import UnoAction
from .cards import UnoSpecials, get_cards

from .. import Game

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

        cards = await get_cards(bot)

        data_users = {user_id: choices(cards, k=6) for user_id in users}
        data_now_user = (await bot.get_chat_member(query.message.chat.id, choice(tuple(data_users)))).user

        data_uno = UnoAction(
            message=query.message,
            bot=bot,
            data=UnoManager(users=data_users, now_user=data_now_user, now_special=UnoSpecials())
        )

        await state.set_state(Game.uno)
        answer = _("Итак, <b>начнём игру.</b>\n\n")

        if data_uno.data.now_user.id == bot.id:
            data_uno.message = await query.message.reply(answer + _("Какая неожиданность, мой ход."))

            from .bot import gen

            data_uno.data = await gen(data_uno)
        else:
            await query.message.reply(
                answer + _("{user}, твой ход.").format(user=get_username(data_uno.data.now_user)),
                reply_markup=k.game_uno_show_cards(),
            )

        print(await state.get_state())
        print(data_uno.data)
        await state.update_data(uno=data_uno.data)
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
