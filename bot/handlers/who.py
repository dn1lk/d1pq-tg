from random import choice

from aiogram import Bot, Router, F, types, flags, html
from aiogram.utils.i18n import I18n, gettext as _

from . import Commands
from .. import filters

router = Router(name='who')
router.message.filter(filters.Command(Commands.WHO.value))


@router.message(F.chat.type == 'private')
async def private_handler(message: types.Message):
    await message.answer(_("This command only works in <b>chats</b>, alas =("))


@router.message(filters.MagicData(F.args))
@flags.sql('members')
async def args_handler(
        message: types.Message,
        bot: Bot,
        command: filters.CommandObject,
        members: list[int] | None,
):
    if members and len(members) > 1:
        args = command.args

        if args[-1] in '?:-,':
            args = args[:-1] + '.'
        elif args[-1] not in '.!':
            args += '.'

        member = await bot.get_chat_member(message.chat.id, choice(members))
        answer = choice(
            (
                _("Hmmm, I think"),
                _("I guess"),
                _("Oh, I admit"),
                _("Maybe it's"),
                _("Wait! It's"),
            )
        ) + f' {member.user} {html.bold(html.quote(args))}'
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
async def no_args_handler(
        message: types.Message,
        i18n: I18n,
        command: filters.CommandObject,
        messages: list[str],
):
    from .help import transform_command, who_handler
    await who_handler(message, i18n, transform_command(command), messages)
