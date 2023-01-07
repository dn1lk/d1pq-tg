from aiogram import Dispatcher, types, html
from aiogram.utils.i18n import gettext as _, lazy_gettext as __

NO_ARGS = __(
    "\n\nWrite a request together with command in one message.\n"
    "For example: <code>/{command} {args}</code>"
)


def get_username(user: types.User = None) -> str:
    if not user:
        return _("User")

    return html.link(html.quote(user.first_name), f'tg://user?id={user.id}')


def get_commands(commands: tuple[types.BotCommand]) -> str:
    return '\n'.join(f'/{command.command} - {command.description}' for command in commands)


def setup(dp: Dispatcher):
    from .games import setup as game_st

    game_st(dp)

    from .settings import setup as setting_st
    from .transitions import setup as transitions_st
    from .command import router as command_rt
    from .error import router as error_rt
    from .other import router as other_rt

    sub_routers = (
        setting_st(),
        command_rt,
        transitions_st(),
        other_rt,
        error_rt,
    )

    for sub_router in sub_routers:
        dp.include_router(sub_router)
