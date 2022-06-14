from typing import Optional

from aiogram import Bot, types
from aiogram.utils.i18n import lazy_gettext as __

NO_ARGS = __("\n\nWrite a request together with command in one message.\nFor example: /{command} {args}")


def get_username(user: types.User) -> str:
    return f'<a href="tg://user?id={user.id}">{user.first_name}</a>'


def get_command_list(
        bot: Bot,
        locale: str,
        index: Optional[slice] = None,
) -> str:
    return '\n'.join(map(lambda command: f'/{command.command} - {command.description}', bot.commands[locale][index]))


def setup(dp):
    from .settings import setup as setting_rt
    from .games import setup as game_rt

    from .action import router as action_rt
    from .command import router as command_rt
    from .error import router as error_rt
    from .other import router as other_rt

    sub_routers = (
        setting_rt(),
        game_rt(),
        command_rt,
        action_rt,
        other_rt,
        error_rt,
    )

    for sub_router in sub_routers:
        dp.include_router(sub_router)
