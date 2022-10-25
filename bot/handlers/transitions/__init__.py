from aiogram import Router

__all__ = 'setup'


def setup() -> Router:
    router = Router(name='transitions')

    from .core import router as all_rt
    from .group import router as chat_rt
    from .private import router as private_rt

    routers = [
        all_rt,
        private_rt,
        chat_rt,
    ]

    for included_router in routers:
        router.include_router(included_router)

    return router
