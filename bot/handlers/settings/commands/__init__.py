from random import choice
from re import findall

from aiogram import Router
from aiogram.utils.i18n import I18n

from bot.utils import markov
from .misc.filter import CustomCommandFilter
from .misc.middleware import CustomCommandsMiddleware


def get_args(i18n: I18n, messages: list | None) -> list[str]:
    if len(messages) > 1:
        args = messages
    else:
        args = sum(markov.get_base(choice(i18n.available_locales), choice(markov.books)).parsed_sentences, [])

    return findall(r'\w+', str(args))


def setup(router: Router):
    from .start import router as start_rt
    from .process import router as process_rt

    sub_routers = (
        process_rt,
        start_rt,
    )

    for sub_router in sub_routers:
        router.include_router(sub_router)
