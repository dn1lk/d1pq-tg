from random import choice

from aiogram import Router, filters, flags, types, Bot, html
from aiogram.utils.i18n import gettext as _, I18n

from bot.utils.database.context import DataBaseContext
from .. import get_username, get_commands

router = Router(name='transitions:group')


@router.my_chat_member(filters.ChatMemberUpdatedFilter(filters.KICKED >> filters.MEMBER))
async def my_return_handler(event: types.ChatMemberUpdated, bot: Bot):
    answer = (
        _("{chat}, we are together again!"),
        _("{chat}, don't kick me anymore =("),
        _("However hello, {chat}!"),
    )

    await bot.send_message(event.chat.id, choice(answer).format(chat=html.quote(event.chat.title)))


@router.my_chat_member(filters.ChatMemberUpdatedFilter(filters.JOIN_TRANSITION))
async def my_join_handler(
        event: types.ChatMemberUpdated,
        bot: Bot,
        i18n: I18n,
        commands: dict[str, tuple[types.BotCommand]]
):
    answer = _(
        "{chat}, hello! Let's start with answering the obvious questions:\n"
        "- What am I? Bot.\n"
        "- What can I do? Some things after which something happens...\n\n"
    )

    commands = get_commands(commands, i18n.current_locale, slice(2))
    await bot.send_message(event.chat.id, answer.format(chat=html.bold(html.quote(event.chat.title))) + commands)


@router.chat_member(filters.ChatMemberUpdatedFilter(filters.JOIN_TRANSITION))
@flags.data('members')
async def join_handler(
        event: types.ChatMemberUpdated,
        bot: Bot,
        db: DataBaseContext,
        members: list | None = None
):
    if members:
        await db.set_data(members=[*members, event.new_chat_member.user.id])

    if event.new_chat_member.user.is_bot:
        answer = (
            _("All bacchanalia, with you {user}!"),
            _("You don't have to clap, {user} is with us."),
            _("Do not meet, now we have {user}!"),
        )

    else:
        answer = (
            _("Greetings, {user}!"),
            _("Welcome, {user}!"),
            _("{user}... Who is it?"),
        )

    await bot.send_message(event.chat.id, choice(answer).format(user=get_username(event.new_chat_member.user)))


@router.chat_member(filters.ChatMemberUpdatedFilter(filters.LEAVE_TRANSITION))
@flags.data('members')
async def leave_handler(
        event: types.ChatMemberUpdated,
        bot: Bot,
        db: DataBaseContext,
        members: set | None = None,
):
    if members and event.new_chat_member.user.id in members:
        members.remove(event.new_chat_member.user.id)
        await db.update_data(members=members)

    if event.new_chat_member.user.is_bot:
        answer = (
            _("Ha, and so be it!"),
            _("Nothing to chat here."),
            _("Bye-bye."),
        )
    else:
        answer = (
            _("I'll miss :(."),
            _("We've lost a great man... Wait, was that a man?"),
            _("Let's remember."),
            _("Get out of here, user!"),
            _("And it all started so nicely..."),
        )

    await bot.send_message(event.chat.id, choice(answer))
