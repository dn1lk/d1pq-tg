from aiogram import types
from aiogram.utils import formatting
from aiogram.utils.i18n import gettext as _

from core import filters
from handlers.commands import CommandTypes


def get_start_content(subject: types.User | types.Chat) -> formatting.Text:
    match subject:
        case types.User():
            _mention = formatting.TextMention(subject.first_name, user=subject)
        case types.Chat():
            _mention = formatting.BlockQuote(subject.title)

    content = formatting.as_marked_section(
        _mention
        + ", "
        + _(
            "hello! Let's start with answering the obvious questions:\n"
            "- What am I? A text-generating bot based on current chat.\n"
            "- What can I do? Some things after which something happens...\n",
        ),
        *(str(command) for command in CommandTypes.start_commands),
    )

    return content


def get_help_content(command: filters.CommandObject, args: str) -> formatting.Text:
    content = formatting.Text(
        _("Write a request together with command in one message.\nFor example:"),
        " ",
        formatting.Code(command.prefix, command.command, " ", args),
    )

    return content
