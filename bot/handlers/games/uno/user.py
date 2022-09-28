import asyncio
from random import choice

from aiogram import Router, F, types, Bot
from aiogram.fsm.context import FSMContext
from aiogram.utils.i18n import gettext as _

from bot.handlers import get_username
from . import DRAW_CARD
from .action import UnoAction
from .cards import UnoColors
from .data import UnoData
from .exceptions import UnoNoUsersException
from .. import keyboards as k

router = Router(name='game:uno:user')


@router.message(F.sticker.set_name == 'uno_cards')
async def user_handler(message: types.Message, bot: Bot, state: FSMContext):
    data = await state.get_data()
    action_uno: UnoAction = UnoAction(message=message, state=state, data=UnoData(**data['uno']))

    card, accept, decline = action_uno.data.card_filter(message.from_user.id, message.sticker)

    if accept:
        for task in asyncio.all_tasks():
            if task.get_name() == str(action_uno.bot):
                task.cancel()
                break

        action_uno.data.timer_amount = 3

        try:
            await action_uno.prepare(card, accept.format(user=get_username(message.from_user)))
        except UnoNoUsersException:
            await action_uno.end()

    elif decline:
        await action_uno.data.add_card(bot, message.chat.id, message.from_user.id)

        data['uno'] = action_uno.data.dict()
        await state.set_data(data)

        await message.reply(decline.format(user=get_username(message.from_user)))


@router.message(F.text == DRAW_CARD)
async def skip_handler(message: types.Message, bot: Bot, state: FSMContext):
    data_uno: UnoData = UnoData(**(await state.get_data())['uno'])

    if message.from_user.id == data_uno.next_user_id:
        action_uno: UnoAction = UnoAction(message=message, state=state, data=data_uno)

        for task in asyncio.all_tasks():
            if task.get_name() == str(action_uno.bot):
                task.cancel()
                break

        await action_uno.skip()
    else:
        await message.reply(
            _(
                "Of course, I don't mind, but now it's {user}'s turn.\nWe'll have to wait =)."
            ).format(user=get_username(await data_uno.get_user(bot, message.chat.id)))
        )


@router.callback_query(k.Games.filter(F.value.in_([color.value for color in UnoColors.names()])))
async def color_handler(query: types.CallbackQuery, state: FSMContext, callback_data: k.Games):
    data_uno: UnoData = UnoData(**(await state.get_data()).get('uno'))

    if query.from_user.id == data_uno.current_user_id:
        data_uno.current_card.color = UnoColors[callback_data.value]

        await query.message.delete_reply_markup()
        await query.answer(
            choice(
                (
                    _("Received."),
                    _("Changing color..."),
                    _("Some variety!"),
                )
            )
        )
        await query.message.edit_text(
            _("{user} changes the color to {emoji} {color}!").format(
                user=get_username(data_uno.current_user_id),
                emoji=data_uno.current_card.color.value,
                color=data_uno.current_card.color.get_color()
            )
        )

        action_uno = UnoAction(message=query.message.reply_to_message, state=state, data=data_uno)
        await action_uno.process()
    else:
        await query.answer(_("Good.\nWhen you'll get a black card, choose this color ;)."))


@router.callback_query(k.Games.filter(F.value == 'uno'))
async def uno_answer(query: types.CallbackQuery, bot: Bot, state: FSMContext):
    data_uno: UnoData = UnoData(**(await state.get_data()).get('uno'))
    uno_user = query.message.entities[0].user if query.message.entities else await bot.get_me()

    for task in asyncio.all_tasks():
        if task is not asyncio.current_task() and task.get_name().endswith(str(uno_user.id) + ":" + "uno"):
            task.cancel()
            break

    await query.message.delete_reply_markup()

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
        await data_uno.add_card(bot, query.message.chat.id, uno_user.id, 2)
        await query.message.edit_text(
            _("{user} gives {uno_user} 2 cards!").format(
                user=get_username(query.from_user),
                uno_user=get_username(uno_user)
            )
        )

    await state.update_data(uno=data_uno.dict())
