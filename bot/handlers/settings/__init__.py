from aiogram import Router, F
from aiogram.fsm.state import StatesGroup, State
from aiogram.utils.i18n import lazy_gettext as __


class Settings(StatesGroup):
    command = State()


UPDATE = __("\n\nUpdate:")
UPDATE_AGAIN = __("\n\nUpdate again:")


def setup():
    from . import keyboards as k

    router = Router(name='settings')
    router.callback_query.filter(k.Settings.filter(F.name))

    from .accuracy import router as accuracy_rt
    from .chance import router as chance_rt
    from .commands import router as commands_rt
    from .data import router as data_rt
    from .locale import router as locale_rt
    from .other import router as other_rt

    sub_routers = (
        other_rt,
        accuracy_rt,
        chance_rt,
        commands_rt,
        locale_rt,
        data_rt,
    )

    for sub_router in sub_routers:
        router.include_router(sub_router)

    return router
