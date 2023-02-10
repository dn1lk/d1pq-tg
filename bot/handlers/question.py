from aiogram import Router, F, types, flags, html
from aiogram.utils.i18n import I18n, gettext as _

from . import Commands, answer_check
from .. import filters
from ..utils import wiki

router = Router(name='question')
router.message.filter(filters.Command(Commands.QUESTION.value))


@router.message(filters.MagicData(F.args))
@flags.chat_action("typing")
async def args_handler(
        message: types.Message,
        i18n: I18n,
        command: filters.CommandObject,
):
    args = html.quote(command.args)
    message = await message.answer(_("Hm, {args}?\nOk, I need to think...").format(args=html.bold(args)))

    if len(command.args) < 20:
        answer = answer_check(await wiki.gen(i18n.current_locale, args))
    else:
        answer = _("Let's do it sooner!")

    await message.answer(answer)


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
    from .help import transform_command, question_handler
    await question_handler(message, i18n, transform_command(command), messages)
