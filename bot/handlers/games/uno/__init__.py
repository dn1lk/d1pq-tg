from aiogram import Router
from aiogram.utils.i18n import lazy_gettext as __

DRAW_CARD = __("Take a card.")


def setup(router: Router):
    from .inline import router as inline_rt
    from .process import router as process_rt
    from .settings import router as settings_rt
    from .start import router as start_rt
    from .transitions import router as action_rt
    from .user import router as user_rt

    sub_routers = (
        user_rt,
        inline_rt,
        settings_rt,
        process_rt,
        start_rt,
        action_rt,
    )

    for sub_router in sub_routers:
        router.include_router(sub_router)
