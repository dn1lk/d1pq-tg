from random import choice
from re import split

from aiogram import Router, F, types, flags, html
from aiogram.utils.i18n import I18n, gettext as _

from bot import filters
from . import CommandTypes
from .. import resolve_text

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
    await message.answer(resolve_text(f'{answer} {html.bold(html.quote(chosen))}'))


@router.message()
@flags.throttling('gen')
@flags.sql('messages')
@flags.chat_action("typing")
async def without_args_handler(
        message: types.Message,
        i18n: I18n,
        command: filters.CommandObject,
        messages: list[str] | None,
):
    from .help import choose_handler
    await choose_handler(message, i18n, command, messages)
