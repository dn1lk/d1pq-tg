from aiogram import F, Router, types
from aiogram.utils import formatting
from aiogram.utils.i18n import gettext as _

from core import filters
from handlers.commands import CommandTypes
from handlers.commands.play import PlayActions

from . import keyboards

router = Router(name="rps:start")
router.message.filter(filters.Command(*CommandTypes.PLAY, magic=F.args.in_(PlayActions.RPS)))


@router.message()
async def start_handler(message: types.Message) -> None:
    assert message.from_user is not None, "wrong user"

    content = formatting.Text(
        _("Eh, classic"),
        ".\n",
        formatting.TextMention(message.from_user.first_name, user=message.from_user),
        ", ",
        _("press the button:"),
    )

    await message.answer(reply_markup=keyboards.rps_keyboard(), **content.as_kwargs())
