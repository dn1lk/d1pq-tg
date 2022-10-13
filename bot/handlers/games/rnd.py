from random import choice

from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from aiogram.utils.i18n import gettext as _

from . import Game

router = Router(name='game:rnd')
router.message.filter(Game.rnd)


@router.message(F.chat.type == 'private', F.text.in_(set(map(str, range(1, 11)))))
async def answer_handler(message: types.Message):
    bot_var = str(choice(range(1, 11)))

    await message.reply(
        _(
            "Ok, so... My choice is {bot_var}."
        ) + "\n" + _("Our numbers matched!") if bot_var == message.text else _("Our numbers don't match =(.")
    )


@router.message(F.text.in_(set(map(str, range(1, 11)))))
async def answer_handler(message: types.Message, state: FSMContext):
    user_var = (await state.get_data()).get('rnd', {})

    if message.from_user.id in user_var.values():
        answer = (
            _("You have already made your choice."),
            _("Cunning, but you already used your try."),
            _("So let's write it down ... Seen in a scam."),
        )
    else:
        if message.text in user_var:
            user_var[message.text].append(message.from_user.id)
        else:
            user_var[message.text] = message.from_user.id

        await state.update_data(rnd=user_var)

        answer = (
            _("Your choice has been accepted."),
            _("Do you really think that I will choose THIS number? Well, let's see ;)."),
            _("So let's write..."),
        )

    await message.reply(choice(answer))


@router.message(F.text.isdigit())
async def mistake_handler(message: types.Message):
    await message.reply(
        choice(
            (
                _("So you won’t guess for sure, choose a emoji from 1 to 10!"),
                _("Somebody can't read. It was clearly written, from 1 to 10!"),
                _("Between 1 and 10, what's so difficult?!"),
            )
        )
    )
