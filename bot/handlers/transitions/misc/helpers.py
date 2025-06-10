import secrets

from aiogram import types
from aiogram.utils import formatting
from aiogram.utils.i18n import gettext as _

from utils import database


async def update_members(main_settings: database.models.MainSettings, *users: types.User) -> None:
    if not main_settings.with_members:
        return

    saved_members = main_settings.members

    user_ids = [user.id for user in users if user.id not in saved_members]
    if user_ids:
        saved_members.extend(user_ids)
        main_settings.members = saved_members


def get_join_content(*users: types.User) -> formatting.Text:
    total_texts = []

    _users = formatting.as_line(
        *(formatting.TextMention(user.first_name, user=user) for user in users),
        sep=", ",
        end="",
    )

    for user in users:
        if user.is_bot:
            texts = (
                (_("All bacchanalia, with you"), " ", _users, "!"),
                (_("You don't have to clap"), ", ", _users, " ", "is with us."),
                (_("Do not meet, now we have"), " ", _users, "!"),
            )
        else:
            texts = (
                (_("Greetings"), ", ", _users, "!"),
                (_("Welcome"), ", ", _users, "!"),
                (_users, "... ", _("Who is it?")),
            )

        total_texts.extend(texts)

    content = formatting.Text(*secrets.choice(total_texts))
    return content


async def remove_member(main_settings: database.models.MainSettings, user_id: int) -> None:
    if not main_settings.with_members:
        return

    saved_members = main_settings.members

    if user_id in saved_members:
        saved_members.remove(user_id)
        main_settings.members = saved_members


def get_leave_content(user: types.User) -> formatting.Text:
    if user.is_bot:
        texts = (
            _("Ha, and so be it!"),
            _("Nothing to chat here."),
            _("Bye-bye."),
        )
    else:
        texts = (
            _("I'll miss. 😭"),
            _("We've lost a great man... Wait, was that a man?"),
            _("Let's remember."),
            _("Get out of here, user!"),
            _("And it all started so nicely..."),
        )

    content = formatting.Text(secrets.choice(texts))
    return content
