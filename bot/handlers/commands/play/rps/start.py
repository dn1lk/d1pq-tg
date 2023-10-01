from aiogram import Router, types, F
from aiogram.utils.i18n import gettext as _

from core import filters
from handlers.commands import CommandTypes
from handlers.commands.play import PlayActions
from . import keyboards

router = Router(name='rps:start')
router.message.filter(filters.Command(*CommandTypes.PLAY, magic=F.args.in_(PlayActions.RPS)))


@router.message()
async def start_handler(message: types.Message):
    answer = _(
        "Eh, classic.\n"
        "{user}, press the button:"
    ).format(user=message.from_user.mention_html())

    await message.answer(answer, reply_markup=keyboards.rps_keyboard())
