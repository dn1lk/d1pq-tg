import secrets

from aiogram import F, Router, flags, types
from aiogram.utils import formatting
from aiogram.utils.i18n import gettext as _

from handlers.commands.play import PlayStates

router = Router(name="process")
router.message.filter(PlayStates.RND)


@router.message(F.text.in_(tuple(map(str, range(1, 11)))))
@flags.timer
async def process_handler(message: types.Message) -> None:
    bot_number = str(secrets.randbelow(9) + 1)
    user_number = message.text

    if user_number == bot_number:
        content = formatting.Text(
            secrets.choice(
                (
                    _("Yes! I have the same number!"),
                    _("Our numbers matched!"),
                    _("Wow, you have extraordinary luck.\nI also chose this number."),
                ),
            ),
        )
    else:
        _bot_number = formatting.Bold(bot_number)
        content = formatting.Text(
            *secrets.choice(
                (
                    (_("Nope. I chose a number"), " ", _bot_number, "."),
                    (_("Alas, I guessed the number"), " ", _bot_number, "."),
                    (_("So our numbers... didn't match. I have"), " ", _bot_number, "."),
                ),
            ),
        )

    await message.reply(**content.as_kwargs())
