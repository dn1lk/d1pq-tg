from aiogram import Router

from .misc import keyboards
from .misc.actions import GPTOptionsActions
from .misc.states import GPTSettingsStates


def setup(parent_router: Router):
    from . import other, temperature

    parent_router.include_routers(
        other.router,
        temperature.router,
    )

    from . import max_tokens

    max_tokens.setup(parent_router)
