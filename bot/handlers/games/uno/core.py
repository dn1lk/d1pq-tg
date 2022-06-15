from random import choice, random, choices

from aiogram import Bot, Router, F, types
from aiogram.dispatcher.fsm.context import FSMContext
from aiogram.dispatcher.fsm.storage.base import StorageKey
from aiogram.utils.i18n import gettext as _

from bot import keyboards as k
from bot.handlers import get_username
from .action import UnoAction
from .cards import UnoSpecials, get_cards
from .manager import UnoManager
from .. import Game, timer, uno_timeout

router = Router(name='game:uno:core')


def start_filter(query: types.CallbackQuery):
    users = [entity.user.id for entity in query.message.entities if entity.user]

    if len(users) > 1:
        return {'users': users}


@router.callback_query(
    k.GamesData.filter(F.value == 'start'),
    F.from_user.id == F.message.entities[1].user.id,
    start_filter
)
async def start_handler(
    query: types.CallbackQuery | types.Message,
    bot: Bot,
    state: FSMContext,
    users: list | None = None
):
    message = query.message if isinstance(query, types.CallbackQuery) else query
    message = await message.delete_reply_markup()

    if not users:
        users = [entity.user.id for entity in message.entities if entity.user]

        if len(users) <= 1:
            return await start_no_users_handler(message)

    if random() < 2 / len(users):
        user = await bot.get_me()
        users.append(user.id)

        await message.edit_text(
            message.html_text + '\n' + get_username(user),
            reply_markup=message.reply_markup
        )
        await message.answer(
            choice(
                (
                    _("Да-да, я тоже играю!"),
                    _("Поиграю с вами."),
                    _("А в игре и я тоже!")
                )
            )
        )

    cards = await get_cards(bot)
    users_dict = {}

    for user_id in set(users):
        users_dict[user_id] = choices(cards, k=6)
        key = StorageKey(
            bot_id=state.key.bot_id,
            chat_id=user_id,
            user_id=user_id,
            destiny=state.key.destiny
        )

        await state.storage.set_state(bot, key, Game.uno)
        await state.storage.update_data(bot, key, {'uno_chat_id': state.key.chat_id})

    data_uno = UnoAction(
        message=message,
        state=state,
        data=UnoManager(
            users=users_dict,
            current_user=(await bot.get_chat_member(message.chat.id, choice(users))).user,
            current_special=UnoSpecials()
        )
    )

    await state.set_state(Game.uno)

    answer = _("Итак, <b>начнём игру.</b>\n\n")

    if data_uno.data.current_user.id == bot.id:
        message = await message.reply(answer + _("Какая неожиданность, мой ход."))

        from .bot import UnoBot

        bot = UnoBot(message=message, bot=bot, data=data_uno.data)
        await bot.gen(state)
    else:
        message = await message.reply(
            answer + _("{user}, твой ход.").format(user=get_username(data_uno.data.current_user)),
            reply_markup=k.game_uno_show_cards(),
        )

        timer(state, uno_timeout, message=message, data_uno=data_uno.data)

    await state.update_data(uno=data_uno.data)


@router.callback_query(k.GamesData.filter(F.value == 'start'), F.from_user.id == F.message.entities[1].user.id)
async def start_no_users_handler(query: types.CallbackQuery | types.Message):
    await query.answer(_("А с кем играть то? =)"))


@router.callback_query(k.GamesData.filter(F.value == 'start'))
async def start_no_owner_handler(query: types.CallbackQuery):
    await query.answer(_("Ты не можешь начать эту игру."))


@router.callback_query(k.GamesData.filter(F.value == 'join'))
async def game_uno_join(query: types.CallbackQuery):
    users = [entity.user.id for entity in query.message.entities if entity.user]

    if query.from_user.id in users[1:]:
        await query.answer(_("Ты уже участвуешь!"))
    else:
        if len(users) == 1:
            text = query.message.html_text.replace(
                get_username(query.message.entities[1].user),
                get_username(query.from_user)
            )
        else:
            text = query.message.html_text

        await query.message.edit_text(
            text + '\n' + get_username(query.from_user),
            reply_markup=query.message.reply_markup
        )

        await query.answer(_("Теперь участников стало на один больше!"))


@router.callback_query(k.GamesData.filter(F.value == 'leave'))
async def game_uno_leave(query: types.CallbackQuery):
    users = [entity.user.id for entity in query.message.entities if entity.user]

    if query.from_user.id in users[1:]:
        users.remove(query.from_user.id)

        await query.message.edit_text(
            query.message.html_text.replace(
                "\n" + get_username(query.from_user),
                "",
            ),
            reply_markup=query.message.reply_markup
        )

        await query.answer(_("Теперь участников стало на один меньше!"))
    else:
        await query.answer(_("Ты ещё не участвуешь!"))
