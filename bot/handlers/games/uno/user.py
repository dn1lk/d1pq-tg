import asyncio
from random import choice

from aiogram import Router, F, types
from aiogram.filters import MagicData
from aiogram.fsm.context import FSMContext
from aiogram.utils.i18n import gettext as _

from bot.handlers import get_username
from . import DRAW_CARD
from .process import UnoData, UnoColors, UnoBot
from .process.middleware import UnoDataMiddleware
from .. import keyboards as k

router = Router(name='game:uno:user')
router.message.outer_middleware(UnoDataMiddleware())
router.callback_query.outer_middleware(UnoDataMiddleware())


@router.message(F.sticker.set_name == 'uno_by_bp1lh_bot', MagicData(F.data_uno))
async def user_handler(message: types.Message, state: FSMContext, data_uno: UnoData):
    card = data_uno.get_card(message.from_user.id, message.sticker)
    accept, decline = data_uno.filter_card(message.from_user.id, card)

    if accept:
        data_uno.current_card = card
        data_uno.timer_amount = 3

        from .process.core import pre
        await pre(message, state, data_uno, accept)
    elif decline:
        data_uno.pick_card(message.from_user)
        await data_uno.update(state)

        await message.reply(decline.format(user=get_username(message.from_user)))


@router.message(F.text == DRAW_CARD)
async def pass_handler(message: types.Message, state: FSMContext, data_uno: UnoData):
    if message.from_user.id == data_uno.current_user_id:
        for task in asyncio.all_tasks():
            if task.get_name().startswith('uno'):
                task.cancel()

        from .process.core import proceed_pass
        await proceed_pass(message, state, data_uno)
    else:
        user = await data_uno.get_user(state)
        await message.reply(
            _(
                "Of course, I don't mind, but now it's {user}'s turn.\n"
                "We'll have to wait =)."
            ).format(user=get_username(user))
        )


@router.callback_query(k.UnoGame.filter(F.value.in_([color.value for color in UnoColors])))
async def color_handler(query: types.CallbackQuery, state: FSMContext, callback_data: k.Games, data_uno: UnoData):
    if query.from_user.id == data_uno.current_user_id:
        data_uno.current_card.color = UnoColors[callback_data.value]

        await query.message.edit_text(
            _("{user} changes the color to {color}!").format(
                user=get_username(query.from_user),
                color=data_uno.current_card.color.word,
            )
        )

        from .process.core import proceed_turn
        await proceed_turn(query.message, state, data_uno)
        await query.answer()
    else:
        await query.answer(_("When you'll get a black card, choose this color ;)"))


@router.callback_query(k.UnoGame.filter(F.value == 'bluff'))
async def bluff_handler(query: types.CallbackQuery, state: FSMContext, data_uno: UnoData):
    if query.from_user.id == data_uno.current_user_id:
        await query.message.edit_reply_markup(k.uno_show_cards(0))

        answer = await data_uno.play_bluff(state)

        from .process.core import post
        await post(query.message, state, data_uno, answer)
        await query.answer(_("You see right through people!"))
    else:
        user = await data_uno.get_user(state, data_uno.current_user_id)
        answer = _("Only {user} can verify the legitimacy of using this card.")

        await query.answer(answer.format(user=user.first_name))


@router.callback_query(k.UnoGame.filter(F.value == 'uno'), MagicData(F.data_uno))
async def uno_handler(query: types.CallbackQuery, state: FSMContext, data_uno: UnoData):
    from .process.core import proceed_uno
    await proceed_uno(query.message, state, data_uno, query.from_user)

    if query.from_user.id == query.message.entities[0].user.id:
        answer = (
            _("On reaction =)."),
            _("Yep!"),
            _("Ok, you won't get cards."),
        )
    else:
        answer = (
            _("Good job!"),
            _("And you don't want to lose =)"),
            _("You will be reminded of it."),
        )

    await query.answer(choice(answer))


@router.callback_query(k.UnoGame.filter(F.value == 'uno'))
async def uno_no_game_handler(query: types.CallbackQuery):
    await query.answer(_("You are not in the game!"))
