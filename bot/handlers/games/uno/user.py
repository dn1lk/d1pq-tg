import asyncio
from random import choice

from aiogram import Router, F, types, Bot, flags
from aiogram.fsm.context import FSMContext
from aiogram.utils.i18n import gettext as _

from bot.handlers import get_username
from . import DRAW_CARD
from .process import UnoData, UnoColors, UnoBot
from .process.core import pre, finish, pass_turn, process
from .process.exceptions import UnoNoUsersException
from .process.middleware import UnoDataMiddleware
from .. import keyboards as k

router = Router(name='game:uno:user')
router.message.outer_middleware(UnoDataMiddleware())
router.callback_query.outer_middleware(UnoDataMiddleware())


async def user_filter(event: types.Message | types.CallbackQuery, data_uno: UnoData):
    if event.from_user.id in data_uno.users:
        return {'data_uno': data_uno}


@router.message(F.sticker.set_name == 'uno_cards', user_filter)
@flags.uno
async def user_handler(message: types.Message, bot: Bot, state: FSMContext, data_uno: UnoData):
    card = data_uno.check_sticker(message.from_user.id, message.sticker)
    accept, decline = data_uno.filter_card(message.from_user.id, card)

    if accept:
        bot = UnoBot(message, state.bot, data_uno)

        for task in asyncio.all_tasks():
            if task.get_name() == str(bot):
                task.cancel()
                break

        data_uno.current_card = card
        data_uno.timer_amount = 3

        try:
            await pre(message, data_uno, state, accept)
        except UnoNoUsersException:
            await finish(message, data_uno, state)
    elif decline:
        data_uno.add_card(bot, message.from_user)
        await state.update_data(uno=data_uno.dict())

        await message.reply(decline.format(user=get_username(message.from_user)))


@router.message(F.text == DRAW_CARD)
@flags.uno
async def skip_handler(message: types.Message, bot: Bot, state: FSMContext, data_uno: UnoData):
    if message.from_user.id == data_uno.current_user_id:
        bot = UnoBot(message, bot, data_uno)

        for task in asyncio.all_tasks():
            if task.get_name() == str(bot):
                task.cancel()
                break

        await pass_turn(message, data_uno, state)
    else:
        user = (await bot.get_chat_member(message.chat.id, data_uno.current_user_id)).user
        await message.reply(
            _("Of course, I don't mind, but now it's {user}'s turn.\nWe'll have to wait =).").format(
                user=get_username(user)
            )
        )


@router.callback_query(k.Games.filter(F.value.in_([color.value for color in UnoColors])))
@flags.uno
async def color_handler(query: types.CallbackQuery, state: FSMContext, callback_data: k.Games, data_uno: UnoData):
    if query.from_user.id == data_uno.current_user_id:
        data_uno.current_card.color = UnoColors[callback_data.value]

        await query.message.edit_text(
            _("{user} changes the color to {emoji} {color}!").format(
                user=get_username(query.from_user),
                emoji=data_uno.current_card.color.value,
                color=data_uno.current_card.color.word,
            )
        )

        await process(query.message.reply_to_message, data_uno, state)
    else:
        await query.answer(_("When you'll get a black card, choose this color ;)."))


@router.callback_query(k.Games.filter(F.value == 'uno'), user_filter)
@flags.uno
async def uno_handler(query: types.CallbackQuery, bot: Bot, state: FSMContext, data_uno: UnoData):
    uno_user = query.message.entities[0].user if query.message.entities else await bot.get_me()

    for task in asyncio.all_tasks():
        if task.get_name().endswith(str(uno_user.id) + ":" + "uno"):
            task.cancel()
            break

    if query.from_user.id == uno_user.id:
        await query.answer(
            choice(
                (
                    _("On reaction =)."),
                    _("Yep!"),
                    _("Ok, you won't get cards."),
                )
            )
        )
    else:
        data_uno.add_card(bot, uno_user, 2)
        await query.message.edit_text(
            _("{user} gives {uno_user} 2 cards!").format(
                user=get_username(query.from_user),
                uno_user=get_username(uno_user)
            )
        )

    await state.update_data(uno=data_uno.dict())


@router.callback_query(k.Games.filter(F.value == 'uno'))
async def uno_no_game_handler(query: types.CallbackQuery):
    await query.answer(_("You are not in the game!"))
