from aiogram import Router, types, F
from aiogram.utils.i18n import gettext as _

from bot.handlers import get_username
from .misc import keyboards as k
from ...settings.commands import CustomCommandFilter

router = Router(name='game:rps:start')
router.message.filter(CustomCommandFilter(commands=['play', 'поиграем'], magic=F.args.in_(('rps', 'кнб'))))


@router.message()
async def start_handler(message: types.Message):
    await message.answer(
        _("Eh, classic. {user}, your turn.").format(user=get_username(message.from_user)),
        reply_markup=k.show_vars()
    )
