from json import dumps
from random import choice
from typing import Optional

from aiogram import Router, Bot, F, filters, types, flags
from aiogram.dispatcher.fsm.context import FSMContext
from aiogram.utils.i18n import I18n, gettext as _

from worker.handlers import get_command_list, USERNAME

router = Router(name='action')


@router.message(content_types=types.ContentType.NEW_CHAT_MEMBERS)
@flags.data('members')
async def on_member_join_handler(
        message: types.Message,
        bot: Bot,
        state: Optional[FSMContext] = None,
        members: Optional[dict] = None
):
    answer = {'user': [], 'bot': []}

    for new_chat_member in message.new_chat_members:
        if new_chat_member.id != bot.id:
            if members:
                members[str(new_chat_member.id)] = new_chat_member.first_name

            user = USERNAME.format(id=new_chat_member.id, name=new_chat_member.first_name)

            if new_chat_member.is_bot:
                answer['bot'].append(user)
            else:
                answer['user'].append(user)

    if answer['bot']:
        await bot.send_message(
            message.chat.id,
            choice(
                (
                    _("All bacchanalia, with you {username}!"),
                    _("You don't have to clap, {username} is with us."),
                    _("Do not meet, now we have {username}!"),
                )
            ).format(username=', '.join(answer['bot'])),
        )

    if answer['bot'] and answer['user']:
        await bot.send_message(
            message.chat.id,
            choice(
                (
                    _("AAAND..."),
                    _("But that's not all!"),
                    _("Well, that's not all... Oh, yes!"),
                )
            )
        )

    if answer['user']:
        await bot.send_message(
            message.chat.id,
            choice(
                (
                    _("Greetings, {username}!"),
                    _("Welcome, {username}!"),
                    _("{username}... Who is it?"),
                )
            ).format(username=', '.join(answer['user'])),
        )

    if members:
        await bot.sql.set_data(message.chat.id, 'members', dumps(members), state)


@router.message(
    filters.MagicData(magic_data=~(F.event.left_chat_member.id == F.bot.id)),
    content_types=types.ContentType.LEFT_CHAT_MEMBER
)
@flags.data('members')
async def on_member_leave_handler(
        message: types.Message,
        bot: Bot,
        state: Optional[FSMContext] = None,
        members: Optional[dict] = None,
):
    answer = {
        False: (
            _("I'll miss :(."),
            _("We've lost a great man... Wait, was that a man?"),
            _("Let's remember."),
            _("Get out of here, user!"),
            _("And it all started so nicely..."),
        ),
        True: (
            _("Ha, and so be it!"),
            _("Nothing to chat here."),
            _("Bye-bye."),
        )
    }

    await bot.send_message(message.chat.id, choice(answer[message.left_chat_member.is_bot]))

    if members and members.get(str(message.left_chat_member.id)):
        del members[str(message.left_chat_member.id)]
        await bot.sql.update_data(message.chat.id, 'members', dumps(members), state)


@router.my_chat_member(member_status_changed=filters.JOIN_TRANSITION)
async def on_me_join_handler(event: types.ChatMemberUpdated, bot: Bot, i18n: I18n):
    await bot.send_message(
        event.chat.id,
        _(
            "{title}, hello! Let's start with answering the obvious questions:\n"
            "- What am I? Bot.\n"
            "- What can I do? Some things after which something happens...\n\n"
        ).format(title=event.chat.title) + get_command_list(bot, i18n.current_locale, slice(2)))


@router.my_chat_member(member_status_changed=filters.LEAVE_TRANSITION)
async def on_me_leave_handler(event: types.ChatMemberUpdated, bot: Bot, state: Optional[FSMContext] = None):
    await bot.sql.del_data(event.chat.id, state)
