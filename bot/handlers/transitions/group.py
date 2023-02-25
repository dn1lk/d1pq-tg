from random import choice

from aiogram import Bot, Router, F, types, enums, flags
from aiogram.utils.i18n import gettext as _

from bot import filters
from bot.utils import database

router = Router(name='transitions:group')
router.my_chat_member.filter(F.chat.type != enums.ChatType.PRIVATE)


async def my_is_not_admin_filter(message: types.Message, bot: Bot):
    member = await bot.get_chat_member(message.chat.id, bot.id)
    return not member.can_manage_chat


@router.my_chat_member(filters.ChatMemberUpdatedFilter(filters.KICKED >> filters.MEMBER))
async def my_return_handler(event: types.ChatMemberUpdated, bot: Bot):
    answer = (
        _("{chat}, we are together again!"),
        _("{chat}, don't kick me anymore =("),
        _("However hello, {chat}!"),
    )

    await bot.send_message(event.chat.id, choice(answer).format(chat=event.chat.mention_html()))


@router.my_chat_member(filters.ChatMemberUpdatedFilter(filters.JOIN_TRANSITION))
async def my_join_handler(event: types.ChatMemberUpdated, bot: Bot):
    chat = event.chat

    from ..commands.start import get_answer
    await bot.send_message(chat.id, get_answer().format(name=chat.mention_html()))


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


async def cat_member(db: database.SQLContext, members: list[int] | None, chat_id: int, *users: types.User):
    if members:
        user_ids = [user.id for user in users if user.id not in members]

        if user_ids:
            await db.members.cat(chat_id, user_ids)


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
@flags.sql('members')
async def join_action_handler(
        event: types.ChatMemberUpdated,
        bot: Bot,
        db: database.SQLContext,
        members: list[int] | None,
):
    user = event.new_chat_member.user
    chat = event.chat

    await cat_member(db, members, chat.id, user)

    answer = join_answer(user)
    await bot.send_message(chat.id, answer.format(user=user.mention_html()))


@router.message(F.new_chat_members, my_is_not_admin_filter)
@flags.sql('members')
async def join_message_handler(
        message: types.Message,
        db: database.SQLContext,
        members: list[int] | None,
):
    users = message.new_chat_members

    await cat_member(db, members, message.chat.id, *users)

    answer = choice([join_answer(user) for user in users])
    await message.answer(answer.format(user=', '.join(user.mention_html() for user in users)))


async def remove_member(db: database.SQLContext, members: list[int] | None, chat_id: int, user_id: int):
    if members and user_id in members:
        await db.members.remove(chat_id, user_id)


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
@flags.sql('members')
async def leave_action_handler(
        event: types.ChatMemberUpdated,
        bot: Bot,
        db: database.SQLContext,
        members: list[int] | None,
):
    user = event.new_chat_member.user
    chat = event.chat

    await remove_member(db, members, chat.id, user.id)

    answer = leave_answer(user)
    await bot.send_message(chat.id, answer)


@router.message(F.left_chat_member, filters.MagicData(F.event.left_chat_member.id != F.bot.id), my_is_not_admin_filter)
@flags.sql('members')
async def leave_message_handler(
        message: types.Message,
        db: database.SQLContext,
        members: list[int] | None,
):
    user = message.left_chat_member
    chat = message.chat

    await remove_member(db, members, chat.id, user.id)

    answer = leave_answer(user)
    await message.answer(answer)
