from random import choice
from re import split

from aiogram import Router, F, types, flags, html
from aiogram.utils.i18n import I18n, gettext as _

from . import Commands, answer_check
from .. import filters

router = Router(name='choose')
router.message.filter(filters.Command(Commands.CHOOSE.value))


@router.message(filters.MagicData(F.args))
async def args_handler(message: types.Message, command: filters.CommandObject):
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
    await message.answer(answer_check(f'{answer} {html.bold(html.quote(chosen))}'))


@router.message()
@flags.throttling('gen')
@flags.sql('messages')
@flags.chat_action("typing")
async def no_args_handler(
        message: types.Message,
        i18n: I18n,
        command: filters.CommandObject,
        messages: list[str] | None,
):
    from .help import transform_command, choose_handler
    await choose_handler(message, i18n, transform_command(command), messages)
