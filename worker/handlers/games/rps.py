from random import choice

from aiogram import Router, F, types
from aiogram.dispatcher.fsm.context import FSMContext
from aiogram.utils.i18n import gettext as _

from worker import keyboards as k
from worker.handlers.games import GameState

router = Router(name='game_rps')


def game_rps_filter(text) -> bool:
    return any(item[1].lower() in text for item in k.get_game_rps_args())


@router.message(F.text.lower().func(game_rps_filter), state=GameState.RPS)
@router.message(F.reply_to_message.text.lower().func(game_rps_filter))
async def game_rps_two_handler(message: types.Message, state: FSMContext):
    bot_var = choice(tuple(k.get_game_rps_args()))
    user_var = message.text.lower()

    wins, loses = (await state.get_data()).get('game_rps', (0, 0))

    again = _("\n\nScore: {loses}-{wins}.\nPlay again?")

    if bot_var[1].lower() in user_var:
        answer = _("Draw.") + again.format(loses=loses, wins=wins)
    elif k.get_game_rps_args()[bot_var][1].lower() in user_var:
        wins += 1
        answer = _("My win!") + again.format(loses=loses, wins=wins)
    else:
        loses += 1
        answer = _("My defeat...") + again.format(loses=loses, wins=wins)

    await state.update_data({'game_rps': (wins, loses)})
    await message.reply(f'{" ".join(bot_var)}! {answer}', reply_markup=k.game_rps())

    if not await state.get_state() == GameState.RPS:
        await state.set_state(GameState.RPS.state)


@router.message(state=GameState.RPS)
async def game_rps_back_handler(message: types.Message, state: FSMContext):
    await state.clear()

    await message.answer(
        choice(
            (
                _("Well don't play with me!"),
                _("I thought we were playing..."),
                _("I won't play with you!"),
            )
        ),
        reply_markup=types.ReplyKeyboardRemove(),
    )
