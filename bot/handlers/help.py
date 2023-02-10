from random import choices

from aiogram import Router, F, types, flags, html
from aiogram.utils.i18n import I18n, gettext as _

from . import Commands, commands_to_str
from .. import filters
from ..utils import markov

router = Router(name='help')
router.message.filter(filters.Command(Commands.HELP.value))


def transform_command(command: filters.CommandObject):
    return filters.CommandObject(
        command.prefix,
        command.command,
        command.mention,
        command.command,
        command.regexp_match,
        command.magic_result,
    )


def get_answer(i18n: I18n, messages: list[str], command: str, args: str | tuple[str]):
    answer = _(
        """
        \n
        \n
        Write a request together with command in one message.\n
        For example: <code>/{command} {args}</code>
        """
    )

    if isinstance(args, tuple):
        args = markov.gen(i18n.current_locale,
                          args[i18n.available_locales.index(i18n.current_locale)], messages,
                          state_size=1, max_size=3)

    return answer.format(command=command, args=args)


@router.message(filters.MagicData(F.args.in_(Commands.QUESTION.value)))
@flags.throttling('gen')
@flags.sql('messages')
@flags.chat_action("typing")
async def question_handler(
        message: types.Message,
        i18n: I18n,
        command: filters.CommandObject,
        messages: list[str] | None,
):
    message = await message.answer(html.bold(_("So what's the question?")))
    await message.answer(get_answer(i18n, messages, command.args,
                                    Commands.QUESTION.value))


@router.message(filters.MagicData(F.args.in_(Commands.CHOOSE.value)))
@flags.throttling('gen')
@flags.sql('messages')
@flags.chat_action("typing")
async def choose_handler(
        message: types.Message,
        i18n: I18n,
        command: filters.CommandObject,
        messages: list[str] | None,
):
    message = await message.answer(html.bold(_("What to choose?")))

    from . import messages_to_words
    await message.answer(get_answer(i18n, messages, command.args,
                                    _(" or ").join(choices(messages_to_words(i18n, messages), k=2))))


@router.message(filters.MagicData(F.args.in_(Commands.WHO.value)))
@flags.throttling('gen')
@flags.sql('messages')
@flags.chat_action("typing")
async def who_handler(
        message: types.Message,
        i18n: I18n,
        command: filters.CommandObject,
        messages: list[str] | None,
):
    message = await message.answer(html.bold(_("Who???")))
    await message.answer(get_answer(i18n, messages, command.args,
                                    Commands.WHO.value))


@router.message(filters.MagicData(F.args.in_(Commands.HISTORY.value)))
@flags.throttling('gen')
@flags.sql('messages')
@flags.chat_action("typing")
async def history_handler(
        message: types.Message,
        i18n: I18n,
        command: filters.CommandObject,
        messages: list[str] | None,
):
    message = await message.answer(html.bold(_("Would you like to read a story?")))
    await message.answer(get_answer(i18n, messages, command.args,
                                    Commands.HISTORY.value))


@router.message()
async def help_handler(message: types.Message, ui_commands: dict[str, tuple[types.BotCommand]], i18n: I18n):
    answer = _(
        """
        List of my main commands - I only accept them together 
        with the required request, in one message:\n
        """
    )
    ui_commands = commands_to_str(ui_commands[i18n.current_locale][3:])
    await message.answer(f'{answer}\n{ui_commands}')
