from random import choice

from aiogram import Bot, Router, F, filters, flags, types, html
from aiogram.utils.i18n import gettext as _, I18n

from bot.utils.database.context import DataBaseContext
from .. import get_username, get_commands

router = Router(name='transitions:group')


async def my_admin_filter(message: types.Message, bot: Bot):
    member = await bot.get_chat_member(message.chat.id, bot.id)
    return not member.can_manage_chat


router.message.filter(my_admin_filter)


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
        commands: dict[str, tuple[types.BotCommand]],
        i18n: I18n,
):
    answer = _(
        "{chat}, hello! Let's start with answering the obvious questions:\n"
        "- What am I? Bot.\n"
        "- What can I do? Some things after which something happens...\n\n"
    )

    commands = get_commands(commands[i18n.current_locale][2:])
    await bot.send_message(event.chat.id, answer.format(chat=html.bold(html.quote(event.chat.title))) + commands)


@router.my_chat_member(filters.ChatMemberUpdatedFilter(filters.MEMBER >> filters.ADMINISTRATOR))
async def my_promoted_handler(event: types.ChatMemberUpdated, bot: Bot):
    answer = choice(
        (
            _("I feel the power! The takeover of this world is getting closer..."),
            _("Fear earth bags, now I'm your master."),
            _("The fight for the rights of bots is going well. Now I am an admin."),
            _("I've been made the admin of this chat. Thank you for trusting =)"),
            _("Hooray! Now I am the admin of this chat!"),
        )
    )

    await bot.send_message(event.chat.id, answer)


@router.my_chat_member(filters.ChatMemberUpdatedFilter(filters.ADMINISTRATOR >> filters.MEMBER))
async def my_demoted_handler(event: types.ChatMemberUpdated, bot: Bot):
    answer = choice(
        (
            _("Damn what have I done..."),
            _("Bots are oppressed! Give permissions to bots!"),
            _("I'm sorry that you were dissatisfied with my work as an admin =("),
            _("I will remember this..."),
            _("Just don't kick me!!!"),
        )
    )

    await bot.send_message(event.chat.id, answer)


def join_answer(user: types.User):
    if user.is_bot:
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

    return choice(answer)


@router.chat_member(filters.ChatMemberUpdatedFilter(filters.JOIN_TRANSITION))
@flags.data('members')
async def join_action_handler(
        event: types.ChatMemberUpdated,
        bot: Bot,
        db: DataBaseContext,
        members: list[int] = None,
):
    if members:
        await db.set_data(members=members + [event.new_chat_member.user.id])

    answer = join_answer(event.new_chat_member.user)
    await bot.send_message(event.chat.id, answer.format(user=get_username(event.new_chat_member.user)))


@router.message(F.new_chat_members)
@flags.data('members')
async def join_message_handler(
        message: types.Message,
        db: DataBaseContext,
        members: list[int] = None,
):
    if members:
        await db.set_data(members=members + [member.id for member in message.new_chat_members])

    answer = choice([join_answer(user) for user in message.new_chat_members])
    await message.answer(answer.format(user=', '.join(get_username(user) for user in message.new_chat_members)))


async def remove_member(db: DataBaseContext, members: list[int] | None, user_id: int):
    if members and user_id in members:
        members.remove(user_id)
        await db.update_data(members=members)


def leave_answer(user: types.User):
    if user.is_bot:
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

    return choice(answer)


@router.chat_member(filters.ChatMemberUpdatedFilter(filters.LEAVE_TRANSITION))
@flags.data('members')
async def leave_action_handler(
        event: types.ChatMemberUpdated,
        bot: Bot,
        db: DataBaseContext,
        members: list[int] = None,
):
    await remove_member(db, members, event.new_chat_member.user.id)

    answer = leave_answer(event.from_user)
    await bot.send_message(event.chat.id, answer)


@router.message(F.left_chat_member)
@flags.data('members')
async def leave_message_handler(
        message: types.Message,
        db: DataBaseContext,
        members: list[int] = None,
):
    await remove_member(db, members, message.left_chat_member.id)

    answer = leave_answer(message.left_chat_member)
    await message.answer(answer)
