import secrets
from collections.abc import Awaitable, Callable
from dataclasses import replace
from typing import Any

from aiogram import F, Router, flags, types
from aiogram.utils import formatting
from aiogram.utils.i18n import gettext as _

from core import filters, helpers
from utils import database

from .misc.helpers import get_help_content
from .misc.types import CommandTypes
from .play import PlayActions

router = Router(name="help")
router.message.filter(filters.Command(*CommandTypes.HELP))


@router.message.middleware
async def command_transform_middleware(
    handler: Callable[[types.TelegramObject, dict[str, Any]], Awaitable[Any]],
    event: types.TelegramObject,
    data: dict[str, Any],
) -> Any:
    """Transform `command` object: command => args"""

    new_data = data.copy()

    command: filters.CommandObject | None = new_data.get("command")
    if command:
        new_data["command"] = replace(command, command=command.args)

    return await handler(event, new_data)


@router.message(filters.MagicData(F.command.args.in_(CommandTypes.PLAY)))
async def play_handler(message: types.Message, command: filters.CommandObject) -> None:
    content = formatting.Bold(_("And what do you want to play?"))
    message = await message.answer(**content.as_kwargs())

    if secrets.randbelow(2) == 1:
        _command = f"{command.prefix}{command.command}"
        content = formatting.Text(
            _("Try to guess the game by writing {command} with its name.").format(command=_command),
        )
    else:
        content = get_help_content(
            command,
            secrets.choice(secrets.choice(list(PlayActions))),
        )

    await message.answer(**content.as_kwargs())


@router.message(filters.MagicData(F.command.args.in_(CommandTypes.CHOOSE)))
@flags.database("gen_settings")
async def choose_handler(
    message: types.Message,
    command: filters.CommandObject,
    gen_settings: database.GenSettings,
) -> None:
    content = formatting.Bold(_("What to choose?"))
    message = await message.answer(**content.as_kwargs())

    if gen_settings.messages:
        to_choice = helpers.get_split_text(gen_settings.messages)
        content = get_help_content(
            command,
            _(" or ").join((secrets.choice(to_choice), secrets.choice(to_choice))),
        )

        await message.answer(**content.as_kwargs())


@router.message(filters.MagicData(F.command.args.in_(CommandTypes.WHO)))
async def who_handler(
    message: types.Message,
    command: filters.CommandObject,
) -> None:
    content = formatting.Bold(_("Who???"))
    message = await message.answer(**content.as_kwargs())

    content = get_help_content(
        command,
        secrets.choice(
            (
                _("will sleep tonight"),
                _("knows the most"),
                _("will prepare everything in time"),
                _("****"),
            ),
        ),
    )

    await message.answer(**content.as_kwargs())


@router.message()
async def help_handler(message: types.Message) -> None:
    content = formatting.as_marked_section(
        _("List of my main commands — I only accept them together with the required request, in one message:\n"),
        *(str(command) for command in CommandTypes.help_commands),
    )

    await message.answer(**content.as_kwargs())
