import asyncio
import secrets

from aiogram import Bot, Router, types
from aiogram.utils import formatting
from aiogram.utils.i18n import gettext as _

from core import filters

router = Router(name="transitions:private")


@router.my_chat_member(filters.ChatMemberUpdatedFilter(filters.KICKED >> filters.MEMBER))
async def my_return_handler(event: types.ChatMemberUpdated, bot: Bot) -> None:
    await asyncio.sleep(1)

    _user = formatting.TextMention(event.from_user.first_name, user=event.from_user)

    content = formatting.Text(
        *secrets.choice(
            (
                (_("Wait, was I kicked"), ", ", _user, "?"),
                (_("Oh, wait. I already wrote this to you..."),),
                (_("I am with you again"), ", ", _user, "!"),
                (_("Oh"), ", ", _user, ", ", _("I got out of your anger?")),
                (_("Ha! I returned"), ", ", _user, "!"),
            ),
        ),
    )

    await bot.send_message(event.chat.id, **content.as_kwargs())


@router.my_chat_member(filters.ChatMemberUpdatedFilter(filters.JOIN_TRANSITION))
async def my_join_handler(_: types.ChatMemberUpdated) -> None:
    pass
