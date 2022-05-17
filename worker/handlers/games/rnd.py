from random import choice

from aiogram import Router, types
from aiogram.dispatcher.fsm.context import FSMContext
from aiogram.utils.i18n import gettext as _

from worker.handlers.games import GameState

router = Router(name='game_rnd')
router.message.filter(state=GameState.RND)


@router.message(text=list(map(lambda number: str(number), range(1, 11))))
async def game_rnd_two_handler(message: types.Message, state: FSMContext):
    data_dict = (await state.get_data()).get('game_rnd', {})

    if str(message.from_user.id) in data_dict:
        answer = (
            _("You have already made your choice."),
            _("Cunning, but you already used your try."),
            _("So let's write it down ... Seen in a scam."),
        )
    else:
        data_dict[str(message.from_user.id)] = (message.from_user.first_name, message.text)
        await state.update_data({'game_rnd': data_dict})

        answer = (
            _("Your choice has been accepted."),
            _("Do you really think that I will choose THIS number? Well, let's see ;)."),
            _("So let's write..."),
        )

    await message.reply(choice(answer))


@router.message(lambda message: message.text.isdigit())
async def game_rnd_three_handler(message: types.Message):
    await message.reply(
        choice(
            (
                _("So you won’t guess for sure, choose a number from 1 to 10!"),
                _("Somebody can't read. It was clearly written, from 1 to 10!"),
                _("Between 1 and 10, what's so difficult?!"),
            )
        )
    )
