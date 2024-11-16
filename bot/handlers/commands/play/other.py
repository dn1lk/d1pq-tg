import secrets

from aiogram import F, Router, types
from aiogram.utils import formatting
from aiogram.utils.i18n import gettext as _

from core import filters
from handlers.commands import CommandTypes

router = Router(name="other")
router.message.filter(filters.Command(*CommandTypes.PLAY))


@router.message(filters.MagicData(F.command.args))
async def with_args_handler(message: types.Message) -> None:
    content = formatting.Text(
        secrets.choice(
            (
                _("Ha! Invalid request, try again."),
                _("Luck is clearly NOT in your favor. You didn't guess the game!"),
                _("The game is not recognized. I'll give it another try!"),
                _("And here it is not. This game has a different name. 😜"),
            ),
        ),
    )

    await message.answer(**content.as_kwargs())


@router.message()
async def without_args_handler(message: types.Message, command: filters.CommandObject) -> None:
    from handlers.commands.help import play_handler

    await play_handler(message, command)
