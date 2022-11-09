from random import choice

from aiogram import Router, F, types, html
from aiogram.fsm.context import FSMContext
from aiogram.utils.i18n import gettext as _

from bot.utils.timer import timer
from .. import Games

router = Router(name='game:rnd:process')
router.message.filter(Games.RND)


@router.message(F.chat.type == 'private', F.text.in_(tuple(map(str, range(1, 11)))))
async def private_handler(message: types.Message, state: FSMContext):
    await timer.cancel(timer.get_name(state, name='game'))
    await state.clear()

    bot_var = str(choice(range(1, 11)))

    answer = _("Ok, so... My choice is {bot_var}.\n").format(bot_var=html.bold(bot_var))
    matched = (_("Our numbers matched!") if bot_var == message.text else _("Our numbers don't match =(."))
    await message.reply(answer + matched)


@router.message(F.text.in_(tuple(map(str, range(1, 11)))))
async def chat_handler(message: types.Message, state: FSMContext):
    user_vars: dict[str, list] = await state.get_data() or {}

    if user_vars and message.from_user.id in sum(user_vars.values(), []):
        answer = (
            _("You have already made your choice."),
            _("Cunning, but you already used your try."),
            _("So let's write it down ... Seen in a scam."),
        )
    else:
        user_vars.setdefault(message.text, []).append(message.from_user.id)
        await state.set_data(user_vars)

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
