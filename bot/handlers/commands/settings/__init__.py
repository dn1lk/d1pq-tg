from aiogram import F, Router, types
from aiogram.utils.i18n import gettext as _

from core import filters
from core.middlewares import DestinySetMiddleware

from .misc import keyboards
from .misc.actions import SettingsActions
from .misc.states import SettingsStates

__all__ = (
    "keyboards",
    "SettingsActions",
    "SettingsStates",
)


router = Router(name="settings")
DestinySetMiddleware().setup(router)


@router.callback_query(keyboards.SettingsData.filter(F.action), filters.IsAdmin(is_admin=False))
async def no_admin_handler(query: types.CallbackQuery):
    await query.answer(_("Only for administrators."))


def setup(parent_router: Router):
    parent_router.include_router(router)

    from . import accuracy, chance, locale, other

    router.include_routers(
        chance.router,
        locale.router,
        accuracy.router,
    )

    from . import commands, gpt, record

    commands.setup(router)
    gpt.setup(router)
    record.setup(router)

    router.include_router(other.router)
