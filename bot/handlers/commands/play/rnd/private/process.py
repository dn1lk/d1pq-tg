from random import choice, randint

from aiogram import Router, F, types, html, flags
from aiogram.utils.i18n import gettext as _

from ... import PlayStates

router = Router(name='process')
router.message.filter(PlayStates.RND)


@router.message(F.text.in_(tuple(map(str, range(1, 11)))))
@flags.timer('play')
async def process_handler(message: types.Message):
    bot_number = str(randint(1, 10))
    user_number = message.text

    if user_number == bot_number:
        answer = choice(
            (
                _("Yes! I have the same number!"),
                _("Our numbers matched!"),
                _("Wow, you have extraordinary luck.\n"
                  "I also chose this number."),
            )
        )
    else:
        answer = choice(
            (
                _("Nope. I chose a number {bot_number}"),
                _("Alas, I guessed the number {bot_number}"),
                _("So our numbers... didn't match. I have {bot_number}.")
            )
        ).format(bot_number=html.bold(bot_number))

    await message.reply(answer)
