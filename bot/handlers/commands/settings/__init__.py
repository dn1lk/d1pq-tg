from aiogram import Router
from aiogram.utils.i18n import lazy_gettext as __

from .misc import keyboards
from .misc.actions import SettingsActions
from .misc.states import SettingsStates

UPDATE = __("\n\nUpdate:")


def setup(parent_router: Router):
    from . import main

    router = main.router
    parent_router.include_router(router)

    from . import accuracy, chance, locale, other

    router.include_routers(
        chance.router,
        locale.router,
        accuracy.router,
    )

    from . import commands, record

    commands.setup(router)
    record.setup(router)

    router.include_router(other.router)
