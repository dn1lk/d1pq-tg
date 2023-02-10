from aiogram import Router, filters
from .misc.middleware import CustomCommandsMiddleware


def setup(router: Router):
    from .start import router as start_rt
    from .process import router as process_rt

    sub_routers = (
        process_rt,
        start_rt,
    )

    for sub_router in sub_routers:
        router.include_router(sub_router)

    from .misc import filter
    filters.Command = filter.CustomCommand
