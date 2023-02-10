from aiogram import Router


def setup(router: Router):
    from .group import router as chat_rt
    from .other import router as other_rt
    from .private import router as private_rt

    routers = (
        chat_rt,
        private_rt,
        other_rt,
    )

    for included_router in routers:
        router.include_router(included_router)

    return router
