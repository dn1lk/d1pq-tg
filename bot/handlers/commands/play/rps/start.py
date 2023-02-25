from aiogram import Router, types, F
from aiogram.utils.i18n import gettext as _

from bot import filters
from . import keyboards
from .. import PlayActions
from ... import CommandTypes

router = Router(name='play:rps:start')
router.message.filter(filters.Command(*CommandTypes.PLAY, magic=F.args.in_(PlayActions.RPS)))


@router.message()
async def rps_handler(message: types.Message):
    answer = _(
        "Eh, classic.\n"
        "{user}, press the button:"
    ).format(user=message.from_user.mention_html())

    await message.answer(answer, reply_markup=keyboards.rps_keyboard())
