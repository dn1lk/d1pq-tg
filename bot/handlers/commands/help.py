from random import choices, random, choice
from typing import Callable, Any, Awaitable

from aiogram import Router, F, types, flags, html
from aiogram.dispatcher.flags import get_flag
from aiogram.utils.i18n import I18n, gettext as _

from bot.core import filters
from bot.core.utils import markov
from .misc.types import CommandTypes, PREFIX

router = Router(name='help')
router.message.filter(filters.Command(*CommandTypes.HELP))


def get_answer(command: filters.CommandObject, args: str):
    answer = _(
        "Write a request together with command in one message.\n"
        "For example: <code>{prefix}{command} {args}</code>"
    )

    return answer.format(prefix=command.prefix, command=command.command, args=args)


def get_args_from_markov(i18n: I18n, messages: list[str], args: CommandTypes):
    return markov.gen(
        i18n.current_locale,
        args.value[i18n.available_locales.index(i18n.current_locale)],
        messages,
        state_size=1, max_size=3
    )


@router.message.middleware()
async def command_transform_middleware(
        handler: Callable[[types.Update, dict[str, Any]], Awaitable[Any]],
        event: types.Update,
        data: dict[str, Any]
):
    if get_flag(data, 'throttling'):
        command = data['command']
        data['command'] = filters.CommandObject(
            command.prefix,
            command.args,
            command.mention,
            command.args,
            command.regexp_match,
            command.magic_result,
        )

    return await handler(event, data)


@router.message(filters.MagicData(F.command.args.in_(CommandTypes.PLAY)))
async def play_handler(message: types.Message, command: filters.CommandObject):
    message = await message.answer(html.bold(_("And what do you want to play?")))

    if random() > 0.5:
        answer = _(
            "Try to guess the game by writing {prefix}{command} with its name."
        ).format(prefix=PREFIX, command=command.command)
    else:
        from .play import PlayActions
        answer = get_answer(command, choice(choice(list(PlayActions))))

    await message.answer(answer)


@router.message(filters.MagicData(F.command.args.in_(CommandTypes.QUESTION)))
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
    await message.answer(get_answer(command,
                                    get_args_from_markov(i18n, messages, CommandTypes.QUESTION)))


@router.message(filters.MagicData(F.command.args.in_(CommandTypes.CHOOSE)))
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

    from .. import messages_to_words
    await message.answer(get_answer(command,
                                    _(" or ").join(choices(messages_to_words(i18n, messages), k=2))))


@router.message(filters.MagicData(F.command.args.in_(CommandTypes.WHO)))
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
    await message.answer(get_answer(command,
                                    get_args_from_markov(i18n, messages, CommandTypes.WHO)))


@router.message(filters.MagicData(F.command.args.in_(CommandTypes.STORY)))
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
    await message.answer(get_answer(command,
                                    get_args_from_markov(i18n, messages, CommandTypes.STORY)))


@router.message(filters.MagicData(F.command.args))
@flags.throttling('gen')
@flags.sql('messages')
@flags.chat_action("typing")
async def history_handler(
        message: types.Message,
        command: filters.CommandObject,
):
    answer = choice(
        (
            _("What is {args}?"),
            _("I don't know what is {args}."),
            _("{args}? I think this is some kind of mistake.")
        )
    ).format(args=html.bold(command.args))

    await message.answer(answer)


@router.message()
async def help_handler(message: types.Message):
    answer = _(
        "List of my main commands — I only accept them together "
        "with the required request, in one message:\n"
    )
    ui_commands = '\n'.join(str(command) for command in list(CommandTypes)[3:-1])
    await message.answer(f'{answer}\n{ui_commands}')
