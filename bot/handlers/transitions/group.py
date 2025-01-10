import secrets

from aiogram import Bot, F, Router, enums, types
from aiogram.utils import formatting
from aiogram.utils.i18n import gettext as _

from core import filters
from handlers.commands.misc.helpers import get_start_content
from utils import database

from .misc.filters import my_is_not_admin_filter
from .misc.helpers import get_join_content, get_leave_content, remove_member, update_members

router = Router(name="transitions:group")
router.message.filter(my_is_not_admin_filter)
router.my_chat_member.filter(F.chat.type != enums.ChatType.PRIVATE)


@router.my_chat_member(filters.ChatMemberUpdatedFilter(filters.KICKED >> filters.MEMBER))
async def my_return_handler(event: types.ChatMemberUpdated, bot: Bot) -> None:
    _chat = formatting.Bold(event.chat.title)

    content = formatting.Text(
        *secrets.choice(
            (
                (_chat, ", ", _("we are together again"), "!"),
                (_chat, ", ", _("don't kick me anymore"), ". 👿"),
                (_("However hello"), ", ", _chat, "!"),
            ),
        ),
    )

    await bot.send_message(event.chat.id, **content.as_kwargs())


@router.my_chat_member(filters.ChatMemberUpdatedFilter(filters.JOIN_TRANSITION))
async def my_join_handler(event: types.ChatMemberUpdated, bot: Bot) -> None:
    content = get_start_content(event.chat)
    await bot.send_message(event.chat.id, **content.as_kwargs())


@router.my_chat_member(filters.ChatMemberUpdatedFilter(filters.MEMBER >> filters.ADMINISTRATOR))
async def my_promoted_handler(event: types.ChatMemberUpdated, bot: Bot) -> None:
    content = formatting.Text(
        secrets.choice(
            (
                _("I feel the power! The takeover of this world is getting closer..."),
                _("Fear earth bags, now I'm your master."),
                _("The fight for the rights of bots is going well. Now I am an admin."),
                _("I've been made the admin of this chat. Thank you for trusting. ☺️"),
                _("Hooray! Now I am the admin of this chat!"),
            ),
        ),
    )

    await bot.send_message(event.chat.id, **content.as_kwargs())


@router.my_chat_member(filters.ChatMemberUpdatedFilter(filters.ADMINISTRATOR >> filters.MEMBER))
async def my_demoted_handler(event: types.ChatMemberUpdated, bot: Bot) -> None:
    content = formatting.Text(
        secrets.choice(
            (
                _("Damn what have I done..."),
                _("Bots are oppressed! Give permissions to bots!"),
                _("I'm sorry that you were dissatisfied with my work as an admin. 🥺"),
                _("I will remember this..."),
                _("Just don't kick me!!!"),
            ),
        ),
    )

    await bot.send_message(event.chat.id, **content.as_kwargs())


@router.chat_member(filters.ChatMemberUpdatedFilter(filters.JOIN_TRANSITION))
async def join_action_handler(
    event: types.ChatMemberUpdated,
    bot: Bot,
    main_settings: database.MainSettings,
) -> None:
    await update_members(main_settings, event.new_chat_member.user)

    content = get_join_content(event.new_chat_member.user)
    await bot.send_message(event.chat.id, **content.as_kwargs())


@router.message(F.new_chat_members)
async def join_message_handler(
    message: types.Message,
    main_settings: database.MainSettings,
) -> None:
    assert message.new_chat_members is not None, "wrong users"

    await update_members(main_settings, *message.new_chat_members)

    content = get_join_content(*message.new_chat_members)
    await message.answer(**content.as_kwargs())


@router.chat_member(filters.ChatMemberUpdatedFilter(filters.LEAVE_TRANSITION))
async def leave_action_handler(
    event: types.ChatMemberUpdated,
    bot: Bot,
    main_settings: database.MainSettings,
) -> None:
    await remove_member(main_settings, event.new_chat_member.user.id)

    content = get_leave_content(event.new_chat_member.user)
    await bot.send_message(event.chat.id, **content.as_kwargs())


@router.message(F.left_chat_member, filters.MagicData(F.event.left_chat_member.id != F.bot.id))
async def leave_message_handler(
    message: types.Message,
    main_settings: database.MainSettings,
) -> None:
    assert message.left_chat_member is not None, "wrong users"

    await remove_member(main_settings, message.left_chat_member.id)

    content = get_leave_content(message.left_chat_member)
    await message.answer(**content.as_kwargs())
