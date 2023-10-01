from random import choice

from aiogram import Bot, Router, F, types, enums
from aiogram.utils.i18n import gettext as _

from core import filters
from core.utils import database

router = Router(name='transitions:group')
router.my_chat_member.filter(F.chat.type != enums.ChatType.PRIVATE)


async def my_is_not_admin_filter(message: types.Message, bot: Bot):
    """ Filter if bot is not admin """

    member = await bot.get_chat_member(message.chat.id, bot.id)
    return not (isinstance(member, types.ChatMemberAdministrator) and member.can_manage_chat)


@router.my_chat_member(filters.ChatMemberUpdatedFilter(filters.KICKED >> filters.MEMBER))
async def my_return_handler(event: types.ChatMemberUpdated, bot: Bot):
    answer = choice(
        (
            _("{chat}, we are together again!"),
            _("{chat}, don't kick me anymore. 👿"),
            _("However hello, {chat}!"),
        )
    ).format(chat=event.chat.mention_html())

    await bot.send_message(event.chat.id, answer)


@router.my_chat_member(filters.ChatMemberUpdatedFilter(filters.JOIN_TRANSITION))
async def my_join_handler(event: types.ChatMemberUpdated, bot: Bot):
    from ..commands.start import get_answer
    answer = get_answer(event.chat)

    await bot.send_message(event.chat.id, answer)


@router.my_chat_member(filters.ChatMemberUpdatedFilter(filters.MEMBER >> filters.ADMINISTRATOR))
async def my_promoted_handler(event: types.ChatMemberUpdated, bot: Bot):
    answer = choice(
        (
            _("I feel the power! The takeover of this world is getting closer..."),
            _("Fear earth bags, now I'm your master."),
            _("The fight for the rights of bots is going well. Now I am an admin."),
            _("I've been made the admin of this chat. Thank you for trusting. ☺️"),
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
            _("I'm sorry that you were dissatisfied with my work as an admin. 🥺"),
            _("I will remember this..."),
            _("Just don't kick me!!!"),
        )
    )

    await bot.send_message(event.chat.id, answer)


async def update_members(main_settings: database.MainSettings, *users: types.User):
    user_ids = [user.id for user in users if user.id not in main_settings.members]

    if user_ids:
        main_settings.members.extend(user_ids)
        await main_settings.save()


def join_answer(user: types.User):
    if user.is_bot:
        answers = (
            _("All bacchanalia, with you {user}!"),
            _("You don't have to clap, {user} is with us."),
            _("Do not meet, now we have {user}!"),
        )
    else:
        answers = (
            _("Greetings, {user}!"),
            _("Welcome, {user}!"),
            _("{user}... Who is it?"),
        )

    return choice(answers)


@router.chat_member(filters.ChatMemberUpdatedFilter(filters.JOIN_TRANSITION))
async def join_action_handler(
        event: types.ChatMemberUpdated,
        bot: Bot,
        main_settings: database.MainSettings,
):
    user = event.new_chat_member.user

    await update_members(main_settings, user)

    answer = join_answer(user).format(user=user.mention_html())
    await bot.send_message(event.chat.id, answer)


@router.message(F.new_chat_members, my_is_not_admin_filter)
async def join_message_handler(
        message: types.Message,
        main_settings: database.MainSettings,
):
    users = message.new_chat_members

    await update_members(main_settings, *users)

    answer = choice([join_answer(user) for user in users]) \
        .format(user=', '.join(user.mention_html() for user in users))

    await message.answer(answer)


async def remove_member(main_settings: database.MainSettings, user_id: int):
    if user_id in main_settings.members:
        main_settings.members.remove(user_id)
        await main_settings.save()


def leave_answer(user: types.User):
    if user.is_bot:
        answers = (
            _("Ha, and so be it!"),
            _("Nothing to chat here."),
            _("Bye-bye."),
        )
    else:
        answers = (
            _("I'll miss. 😭"),
            _("We've lost a great man... Wait, was that a man?"),
            _("Let's remember."),
            _("Get out of here, user!"),
            _("And it all started so nicely..."),
        )

    return choice(answers)


@router.chat_member(filters.ChatMemberUpdatedFilter(filters.LEAVE_TRANSITION))
async def leave_action_handler(
        event: types.ChatMemberUpdated,
        bot: Bot,
        main_settings: database.MainSettings,
):
    user = event.new_chat_member.user

    await remove_member(main_settings, user.id)

    answer = leave_answer(user)
    await bot.send_message(event.chat.id, answer)


@router.message(F.left_chat_member, filters.MagicData(F.event.left_chat_member.id != F.bot.id), my_is_not_admin_filter)
async def leave_message_handler(
        message: types.Message,
        main_settings: database.MainSettings,
):
    user = message.left_chat_member

    await remove_member(main_settings, user.id)

    answer = leave_answer(user)
    await message.answer(answer)
