from dataclasses import replace
from random import choices, random, choice
from typing import Callable, Any, Awaitable

from aiogram import Router, F, types, html, flags
from aiogram.utils.i18n import gettext as _

from core import filters, helpers
from core.utils import database
from .misc.types import CommandTypes

router = Router(name='help')
router.message.filter(filters.Command(*CommandTypes.HELP))


def get_answer(command: filters.CommandObject, args: str):
    answer = _(
        "Write a request together with command in one message.\n"
        "For example: <code>{prefix}{command} {args}</code>"
    ).format(prefix=command.prefix, command=command.command, args=args)

    return answer


@router.message.middleware()
async def command_transform_middleware(
        handler: Callable[[types.Update, dict[str, Any]], Awaitable[Any]],
        event: types.Update,
        data: dict[str, Any]
):
    """ Transform `command` object: command => args """

    command: filters.CommandObject | None = data.get('command')

    if command:
        data['command'] = replace(command, command=command.args)

    return await handler(event, data)


@router.message(filters.MagicData(F.command.args.in_(CommandTypes.PLAY)))
async def play_handler(message: types.Message, command: filters.CommandObject):
    message = await message.answer(html.bold(_("And what do you want to play?")))

    if random() > 0.5:
        answer = _(
            "Try to guess the game by writing {prefix}{command} with its name."
        ).format(prefix=command.prefix, command=command.command)
    else:
        from .play import PlayActions
        answer = get_answer(
            command,
            choice(choice(list(PlayActions)))
        )

    await message.answer(answer)


@router.message(filters.MagicData(F.command.args.in_(CommandTypes.CHOOSE)))
@flags.database('gen_settings')
async def choose_handler(
        message: types.Message,
        command: filters.CommandObject,
        gen_settings: database.GenSettings,
):
    message = await message.answer(html.bold(_("What to choose?")))

    answer = get_answer(
        command,
        _(" or ").join(choices(helpers.get_split_text(gen_settings.messages), k=2))
    )

    await message.answer(answer)


@router.message(filters.MagicData(F.command.args.in_(CommandTypes.WHO)))
async def who_handler(
        message: types.Message,
        command: filters.CommandObject,
):
    message = await message.answer(html.bold(_("Who???")))
    answer = get_answer(
        command,
        choice(
            (
                _("will sleep tonight"),
                _("knows the most"),
                _("will prepare everything in time"),
                _("****"),
            )
        )
    )

    await message.answer(answer)


@router.message(filters.MagicData(F.command.args))
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

    ui_commands = '\n'.join(str(command) for command in CommandTypes.help_commands)
    await message.answer(f'{answer}\n{ui_commands}')
