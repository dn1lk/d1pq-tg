from random import choice

from aiogram import Router, F, types, html
from aiogram.fsm.context import FSMContext
from aiogram.utils.i18n import gettext as _

from . import Games

router = Router(name='game:rnd')
router.message.filter(Games.rnd)


@router.message(F.chat.type == 'private', F.text.in_(set(map(str, range(1, 11)))))
async def private_handler(message: types.Message):
    bot_var = str(choice(range(1, 11)))

    answer = _("Ok, so... My choice is {bot_var}.\n").format(bot_var=html.bold(bot_var))
    matched = (_("Our numbers matched!") if bot_var == message.text else _("Our numbers don't match =(."))
    await message.reply(answer + matched)


@router.message(F.text.in_(set(map(str, range(1, 11)))))
async def answer_handler(message: types.Message, state: FSMContext):
    user_var: dict[str, list] = (await state.get_data()).get('rnd', {})

    if message.from_user.id in sum(user_var.values(), []):
        answer = (
            _("You have already made your choice."),
            _("Cunning, but you already used your try."),
            _("So let's write it down ... Seen in a scam."),
        )
    else:
        if message.text in user_var:
            user_var[message.text].append(message.from_user.id)
        else:
            user_var[message.text] = [message.from_user.id]

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
