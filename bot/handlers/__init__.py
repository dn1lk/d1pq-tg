from aiogram import Dispatcher, types, html
from aiogram.utils.i18n import lazy_gettext as __

__all__ = 'NO_ARGS', 'setup', 'get_username', 'get_commands'

NO_ARGS = __("\n\nWrite a request together with command in one message.\nFor example: <code>/{command} {args}</code>")


def get_username(user: types.User) -> str:
    return html.link(html.quote(user.first_name), f"tg://user?id={user.id}")


def get_commands(commands: dict[str, tuple[types.BotCommand]], locale: str, index: slice | None = None) -> str:
    return '\n'.join(f'/{command.command} - {command.description}' for command in commands[locale][index])


def setup(dp: Dispatcher):
    from .settings import setup as setting_rt
    from .games import setup as game_rt
    from .transitions import setup as transitions_rt

    from .command import router as command_rt
    from .error import router as error_rt
    from .other import router as other_rt

    sub_routers = (
        setting_rt(),
        game_rt(),
        command_rt,
        transitions_rt(),
        other_rt,
        error_rt,
    )

    for sub_router in sub_routers:
        dp.include_router(sub_router)
