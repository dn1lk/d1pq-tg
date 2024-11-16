import secrets

from aiogram import Bot, F, Router, enums, types
from aiogram.utils import formatting
from aiogram.utils.i18n import I18n
from aiogram.utils.i18n import gettext as _

from core import filters, helpers
from handlers.commands.misc.types import PREFIX
from utils import database

from . import CommandTypes

router = Router(name="who")
router.message.filter(filters.Command(*CommandTypes.WHO))


@router.message(F.chat.type == enums.ChatType.PRIVATE)
async def private_handler(message: types.Message) -> None:
    content = formatting.Text(_("This command only works in"), " ", formatting.Bold(_("chats")), ", ", _("alas. 😥"))
    await message.answer(**content.as_kwargs())


@router.message(filters.MagicData(F.args))
async def with_args_handler(
    message: types.Message,
    bot: Bot,
    command: filters.CommandObject,
    main_settings: database.MainSettings,
) -> None:
    assert command.args is not None, "wrong command args"

    if main_settings.members:
        if len(main_settings.members) > 1:
            member = await bot.get_chat_member(message.chat.id, secrets.choice(main_settings.members))

            content = formatting.Text(
                secrets.choice(
                    (
                        _("Hmmm, I think"),
                        _("I guess"),
                        _("Oh, I admit"),
                        _("Maybe it's"),
                        _("Wait! It's"),
                    ),
                ),
                " ",
                formatting.TextMention(member.user.first_name, user=member.user),
                formatting.Bold(helpers.resolve_text(command.args)),
            )
        else:
            content = formatting.Text(
                secrets.choice(
                    (
                        _("Oh, I don't know you guys... Give me a time."),
                        _("Does anyone else want to enter this command?"),
                        _("Is there anyone else in this chat besides you?"),
                    ),
                ),
            )
    else:
        content = formatting.Text(
            formatting.Italic(_("This command requires permission to record chat participants.")),
            "\n\n",
            formatting.BotCommand(PREFIX, CommandTypes.SETTINGS[0]),
            " — ",
            _("give permission"),
            ".",
        )

    await message.answer(**content.as_kwargs())


@router.message()
async def without_args_handler(
    message: types.Message,
    i18n: I18n,
    command: filters.CommandObject,
    messages: list[str],
) -> None:
    from .help import who_handler

    await who_handler(message, i18n, command, messages)
