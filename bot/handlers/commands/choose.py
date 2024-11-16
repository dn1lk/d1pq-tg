import secrets
from re import split

from aiogram import F, Router, flags, types
from aiogram.utils import formatting
from aiogram.utils.i18n import gettext as _

from core import filters, helpers
from utils import database

from . import CommandTypes

router = Router(name="choose")
router.message.filter(filters.Command(*CommandTypes.CHOOSE))


@router.message(filters.MagicData(F.command.args))
async def with_args_handler(message: types.Message, command: filters.CommandObject) -> None:
    assert command.args is not None, "wrong command args"

    _chosen = secrets.choice(split(r"\W+or\W+|\W+или\W+|\W{2,}", command.args))
    _chosen = helpers.resolve_text(_chosen)
    content = formatting.Text(
        secrets.choice(
            (
                "",
                _("I choose"),
                _("Hm,"),
                _("Difficult choice. Let there be"),
                _("Why are you asking me? Well I choose"),
            ),
        ),
        " ",
        formatting.Bold(_chosen),
    )

    await message.answer(**content.as_kwargs())


@router.message()
@flags.database("gen_settings")
async def without_args_handler(
    message: types.Message,
    command: filters.CommandObject,
    gen_settings: database.GenSettings,
) -> None:
    from .help import choose_handler

    await choose_handler(message, command, gen_settings)
