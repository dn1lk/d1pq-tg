from typing import Optional

from aiogram import Bot, Dispatcher
from aiogram.dispatcher.fsm.strategy import FSMStrategy
from aiogram.utils.i18n import lazy_gettext as __

USERNAME = "<a href='tg://user?id={id}'>{name}</a>"

NO_ARGS = __("\n\nWrite a request together with command in one message.\nFor example: /{command} {args}")


def get_command_list(
        bot: Bot,
        locale: str,
        index: Optional[slice] = None,
) -> str:
    return '\n'.join(map(lambda command: f'/{command.command} - {command.description}', bot.commands[locale][index]))


def setup():
    dp = Dispatcher(name='dispatcher', fsm_strategy=FSMStrategy.CHAT)

    from .settings import setup as settings_rt
    from .games import setup as games_rt

    from .actions import router as actions_rt
    from .commands import router as commands_rt
    from .errors import router as errors_rt
    from .others import router as others_rt

    sub_routers = (
        settings_rt(),
        games_rt(),
        commands_rt,
        actions_rt,
        others_rt,
        errors_rt,
    )

    for sub_router in sub_routers:
        dp.include_router(sub_router)

    return dp
