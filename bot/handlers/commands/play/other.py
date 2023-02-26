from random import choice

from aiogram import Router, types, F
from aiogram.utils.i18n import gettext as _

from bot import filters
from .. import CommandTypes

router = Router(name='play:other')
router.message.filter(filters.Command(*CommandTypes.PLAY))


@router.message(filters.MagicData(F.command.args))
async def with_args_handler(message: types.Message):
    await message.answer(
        choice(
            (
                _("Ha! Invalid request, try again."),
                _("Luck is clearly NOT in your favor. You didn't guess the game!"),
                _("The game is not recognized. I'll give it another try!"),
                _("And here it is not. This game has a different name ;)."),
            )
        )
    )


@router.message()
async def without_args_handler(message: types.Message, command: filters.CommandObject):
    from ..help import play_handler
    await play_handler(message, command)
