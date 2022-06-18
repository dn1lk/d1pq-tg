from random import choice

from aiogram import Router, F, types
from aiogram.dispatcher.fsm.context import FSMContext
from aiogram.utils.i18n import gettext as _

from bot import keyboards as k
from . import Game, timer, close_timeout

router = Router(name='game:rps')


def game_rps_answer_filter(text) -> bool:
    return any(item[1].lower() in text for item in k.get_game_rps_args())


router.message.filter(F.text.lower().func(game_rps_answer_filter))


@router.message(Game.rps)
async def game_rps_answer_handler(message: types.Message, state: FSMContext):
    bot_var = choice(tuple(k.get_game_rps_args()))
    user_var = message.text.lower()

    data = await state.get_data()
    wins, loses = data['rps']

    if bot_var[1].lower() in user_var:
        result = _("Draw.")
    elif k.get_game_rps_args()[bot_var][1].lower() in user_var:
        wins += 1
        result = _("My win!")
    else:
        loses += 1
        result = _("My defeat...")

    answer = _("Score: {loses}-{wins}.\nPlay again?").format(loses=loses, wins=wins)
    await message.reply(" ".join(bot_var) + "! " + result + "\n\n" + answer, reply_markup=k.game_rps())

    await state.update_data(rps=(wins, loses))
    timer(state, close_timeout, message=message)


@router.message(F.reply_to_message.text.lower().func(game_rps_answer_filter))
async def game_rps_reply_handler(message: types.Message, state: FSMContext):
    await state.set_state(Game.rps)
    await state.update_data(rps=(0, 0))
    return await game_rps_answer_handler(message, state)
