from random import choice

from aiogram import Router, Bot, F, filters, types, flags
from aiogram.utils.i18n import I18n, gettext as _

from bot.utils.database.context import DataBaseContext
from . import get_username, get_command_list

router = Router(name='action')


@router.my_chat_member(~(F.chat.type == 'private'), member_status_changed=filters.JOIN_TRANSITION)
async def on_me_join_handler(event: types.ChatMemberUpdated, bot: Bot, i18n: I18n):
    await bot.send_message(
        event.chat.id,
        _(
            "{title}, hello! Let's start with answering the obvious questions:\n"
            "- What am I? Bot.\n"
            "- What can I do? Some things after which something happens..."
        ).format(title=event.chat.title) + "\n\n" + get_command_list(bot, i18n.current_locale, slice(2)))


@router.my_chat_member(member_status_changed=filters.LEAVE_TRANSITION)
async def on_me_leave_handler(_, db: DataBaseContext):
    await db.clear()


@router.message(
    content_types=types.ContentType.LEFT_CHAT_MEMBER,
    magic_data=F.event.left_chat_member.id == F.bot.id,
)
async def on_me_leave_message_handler(_):
    pass


@router.message(content_types=types.ContentType.NEW_CHAT_MEMBERS)
@flags.data('members')
async def on_member_join_handler(
        message: types.Message,
        bot: Bot,
        db: DataBaseContext,
        members: list | None = None
):
    answer = {'user': [], 'bot': []}

    for new_chat_member in message.new_chat_members:
        if new_chat_member.id != bot.id:
            if members:
                await db.set_data(members=members + [new_chat_member.id])

            user = get_username(new_chat_member)

            if new_chat_member.is_bot:
                answer['bot'].append(user)
            else:
                answer['user'].append(user)

    if answer['bot']:
        await message.answer(
            choice(
                (
                    _("All bacchanalia, with you {user}!"),
                    _("You don't have to clap, {user} is with us."),
                    _("Do not meet, now we have {user}!"),
                )
            ).format(user=', '.join(answer['bot'])),
        )

    if answer['bot'] and answer['user']:
        await message.answer(
            choice(
                (
                    _("AAAND..."),
                    _("But that's not all!"),
                    _("Well, that's not all... Oh, yes!"),
                )
            )
        )

    if answer['user']:
        await message.answer(
            choice(
                (
                    _("Greetings, {user}!"),
                    _("Welcome, {user}!"),
                    _("{user}... Who is it?"),
                )
            ).format(user=', '.join(answer['user'])),
        )


@router.message(content_types=types.ContentType.LEFT_CHAT_MEMBER)
@flags.data('members')
async def on_member_leave_handler(
        message: types.Message,
        db: DataBaseContext,
        members: list | None = None,
):
    if members and message.left_chat_member.id in members:
        members.remove(message.left_chat_member.id)
        await db.update_data(members=members)

    if message.left_chat_member.is_bot:
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

    await message.answer(choice(answer))
