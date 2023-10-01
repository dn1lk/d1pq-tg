from random import choice
from re import split

from aiogram import Router, F, types, html, flags
from aiogram.utils.i18n import gettext as _

from core import filters, helpers
from core.utils import database
from . import CommandTypes

router = Router(name='choose')
router.message.filter(filters.Command(*CommandTypes.CHOOSE))


@router.message(filters.MagicData(F.args))
async def with_args_handler(message: types.Message, command: filters.CommandObject):
    answer = choice(
        (
            "",
            _("I choose"),
            _("Hm,"),
            _("Difficult choice. Let there be"),
            _("Why are you asking me? Well I choose"),
        )
    )

    chosen = choice(split(r'\W+or\W+|\W+или\W+|\W{2,}', command.args))
    await message.answer(helpers.resolve_text(f'{answer} {html.bold(html.quote(chosen))}'))


@router.message()
@flags.database('gen_settings')
async def without_args_handler(
        message: types.Message,
        command: filters.CommandObject,
        gen_settings: database.GenSettings,
):
    from .help import choose_handler
    await choose_handler(message, command, gen_settings)
