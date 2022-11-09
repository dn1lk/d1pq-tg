from aiogram import Router, Bot, F, types, html
from aiogram.fsm.context import FSMContext
from aiogram.utils.i18n import gettext as _

from bot.utils.timer import timer
from .misc import UnoData, keyboards as k
from .settings import UnoDifficulty, UnoMode, UnoAdd
from .. import Games
from ... import get_username
from ...settings.commands import CustomCommandFilter

router = Router(name='game:uno:start')
router.message.filter(CustomCommandFilter(commands=['play', 'поиграем'], magic=F.args.in_(('uno', 'уно'))))


@router.message(Games.UNO)
async def uno_join_handler(message: types.Message, state: FSMContext):
    data_uno = await UnoData.get_data(state)

    if message.from_user.id in data_uno.users:
        await message.reply(_("You already in the game."))
    elif len(data_uno.users) == 10:
        await message.reply(_("Already 10 people are playing in the game."))
    else:
        data_uno.users[message.from_user.id] = await data_uno.add_user(state, message.from_user.id, data_uno.deck)
        await data_uno.set_data(state)

        await message.answer(_("{user} join to current game.").format(user=get_username(message.from_user)))


@router.message()
async def uno_handler(message: types.Message, bot: Bot, state: FSMContext):
    answer = _(
        "<b>Let's play UNO?</b>\n\n"
        "One minute to make a decision!\n"
        "Difficulty: {difficulty}.\n"
        "Mode: {mode}.\n\n"
        "{additives}\n\n"
        "<b>Already in the game:</b>\n"
        "{user}"
    )

    message = await message.answer(
        answer.format(
            user=get_username(message.from_user),
            difficulty=html.bold(UnoDifficulty.NORMAL.word),
            mode=html.bold(UnoMode.FAST.word),
            additives='\n'.join(f'{name}: {html.bold(UnoAdd.ON.word)}.' for name in UnoAdd.get_names()),
        ),
        reply_markup=k.setup(),
    )

    from .process import start_timer
    timer.create(state, start_timer, name='game', message=message, bot=bot)
