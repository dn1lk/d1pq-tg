from random import choice

from aiogram import Bot, Router, F, types, enums, flags, html
from aiogram.utils.i18n import I18n, gettext as _

from bot.core import filters
from . import CommandTypes
from .. import resolve_text

router = Router(name='who')
router.message.filter(filters.Command(*CommandTypes.WHO))


@router.message(F.chat.type == enums.ChatType.PRIVATE)
async def private_handler(message: types.Message):
    await message.answer(_("This command only works in <b>chats</b>, alas =("))


@router.message(filters.MagicData(F.args))
@flags.sql('members')
async def with_args_handler(
        message: types.Message,
        bot: Bot,
        command: filters.CommandObject,
        members: list[int] | None,
):
    if members and len(members) > 1:
        member = await bot.get_chat_member(message.chat.id, choice(members))
        answer = resolve_text(
            choice(
                (
                    _("Hmmm, I think"),
                    _("I guess"),
                    _("Oh, I admit"),
                    _("Maybe it's"),
                    _("Wait! It's"),
                )
            ) + f' {member.user.mention_html()} {html.bold(html.quote(command.args))}'
        )

    elif members:
        answer = choice(
            (
                _("Oh, I don't know you guys... Give me a time."),
                _("Does anyone else want to enter this command?"),
                _("Is there anyone else in this chat besides you?")
            )
        )

    else:
        answer = _(
            "<b>This command requires permission to record chat participants.</b>\n"
            "\n"
            "/settings - give permission."
        )

    await message.answer(answer)


@router.message()
@flags.throttling('gen')
@flags.sql('messages')
@flags.chat_action("typing")
async def without_args_handler(
        message: types.Message,
        i18n: I18n,
        command: filters.CommandObject,
        messages: list[str] | None,
):
    from .help import who_handler
    await who_handler(message, i18n, command, messages)
