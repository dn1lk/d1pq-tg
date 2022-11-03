import asyncio
from random import choice

from aiogram import Router, F, types
from aiogram.filters import MagicData
from aiogram.fsm.context import FSMContext
from aiogram.utils.i18n import gettext as _

from bot.handlers import get_username
from . import DRAW_CARD
from .process import UnoData, UnoColors
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


@router.message(
    MagicData(F.event.from_user.id == F.data_uno.current_user_id),
    F.text == DRAW_CARD,
)
async def pass_handler(message: types.Message, state: FSMContext, data_uno: UnoData):
    from .process.core import proceed_pass
    await proceed_pass(message, state, data_uno)


@router.message(F.text == DRAW_CARD)
async def pass_no_current_handler(message: types.Message, state: FSMContext, data_uno: UnoData):
    user = await data_uno.get_user(state)
    await message.reply(
        _(
            "Of course, I don't mind, but now it's {user}'s turn.\n"
            "We'll have to wait =)."
        ).format(user=get_username(user))
    )


@router.message(
    MagicData(F.event.from_user.id == F.data_uno.current_user_id),
    F.entities.func(lambda entities: entities[0].type in ('mention', 'text_mention')),
)
async def seven_handler(message: types.Message, state: FSMContext, data_uno: UnoData):
    user = message.entities[0].user

    if not user:
        for user_id in data_uno.users:
            user = await data_uno.get_user(state, user_id)

            if user.username == message.entities[0].extract_from(message.text):
                seven_user = user
    else:
        seven_user = user if user in data_uno.users else None

    if seven_user:
        answer = data_uno.play_seven(message.from_user, seven_user)
        await data_uno.update(state)

        await message.answer(
            answer.format(
                user=get_username(message.from_user),
                seven_user=get_username(seven_user),
            )
        )

    else:
        await message.answer(_("{user} is not playing with us.").format(user=get_username(seven_user)))


@router.callback_query(
    MagicData(F.event.from_user.id == F.data_uno.current_user_id),
    k.UnoGame.filter(F.value.in_([color.value for color in UnoColors])),
)
async def color_handler(query: types.CallbackQuery, state: FSMContext, callback_data: k.Games, data_uno: UnoData):
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


@router.callback_query(k.UnoGame.filter(F.value.in_([color.value for color in UnoColors])))
async def color_no_current_handler(query: types.CallbackQuery):
    await query.answer(_("When you'll get a black card, choose this color ;)"))


@router.callback_query(
    MagicData(F.event.from_user.id == F.data_uno.current_user_id),
    k.UnoGame.filter(F.value == 'bluff'),
)
async def bluff_handler(query: types.CallbackQuery, state: FSMContext, data_uno: UnoData):
    await query.message.edit_reply_markup(k.uno_show_cards(0))

    answer = await data_uno.play_bluff(state)

    from .process.core import post
    await post(query.message, state, data_uno, answer)

    await query.answer(_("You see right through people!"))


@router.callback_query(k.UnoGame.filter(F.value == 'bluff'))
async def bluff_no_current_handler(query: types.CallbackQuery, state: FSMContext, data_uno: UnoData):
    user = await data_uno.get_user(state, data_uno.current_user_id)
    answer = _("Only {user} can verify the legitimacy of using this card.")

    await query.answer(answer.format(user=user.first_name))


@router.callback_query(
    k.UnoGame.filter(F.value == 'uno'),
    MagicData(F.event.from_user.func(lambda user: F.data_uno.users.get(user.id)))
)
async def uno_handler(query: types.CallbackQuery, state: FSMContext, data_uno: UnoData):
    from .process import UnoBot
    bot = UnoBot(query.message, state, data_uno)

    for task in asyncio.all_tasks():
        if task.get_name() == f'{bot}:uno':
            task.cancel()
            break
    else:
        return query.answer(_("Next time be faster!"))

    from .process.core import proceed_uno

    try:
        await proceed_uno(query.message, state, data_uno, query.from_user)

        answer = (
            _("Good job!"),
            _("And you don't want to lose =)"),
            _("You will be reminded of it."),
        )

    except asyncio.CancelledError:
        answer = (
            _("On reaction =)."),
            _("Yep!"),
            _("Ok, you won't get cards."),
        )

    await query.answer(choice(answer))


@router.callback_query(k.UnoGame.filter(F.value == 'uno'))
async def uno_no_game_handler(query: types.CallbackQuery):
    await query.answer(_("You are not in the game!"))
