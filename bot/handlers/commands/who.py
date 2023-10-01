from random import choice

from aiogram import Bot, Router, F, types, enums, html
from aiogram.utils.i18n import I18n, gettext as _

from core import filters, helpers
from core.utils import database
from . import CommandTypes

router = Router(name='who')
router.message.filter(filters.Command(*CommandTypes.WHO))


@router.message(F.chat.type == enums.ChatType.PRIVATE)
async def private_handler(message: types.Message):
    await message.answer(_("This command only works in <b>chats</b>, alas. 😥"))


@router.message(filters.MagicData(F.args))
async def with_args_handler(
        message: types.Message,
        bot: Bot,
        command: filters.CommandObject,
        main_settings: database.MainSettings,
):
    if len(main_settings.members) > 1:
        member = await bot.get_chat_member(message.chat.id, choice(main_settings.members))
        answer = helpers.resolve_text(
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

    elif main_settings.members:
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
            "/settings — give permission."
        )

    await message.answer(answer)


@router.message()
async def without_args_handler(
        message: types.Message,
        i18n: I18n,
        command: filters.CommandObject,
        messages: list[str],
):
    from .help import who_handler
    await who_handler(message, i18n, command, messages)
