from random import choice

from aiogram import Router, types, flags, html
from aiogram.utils.i18n import I18n, gettext as _

from . import Commands, answer_check
from .. import filters
from ..utils import markov

router = Router(name='history')
router.message.filter(filters.Command(Commands.HISTORY.value))


@router.message()
@flags.throttling('gen')
@flags.sql('messages')
@flags.chat_action("typing")
async def args_handler(
        message: types.Message,
        i18n: I18n,
        command: filters.CommandObject,
        messages: list[str] | None,
):
    if command.args:
        text = html.quote(command.args)
    else:
        text = choice(messages or [_("history")])

    answer = markov.gen(i18n.current_locale, text, messages, tries=150000, min_words=50)
    await message.answer(answer_check(f'{_("In short,")} {answer}'))
