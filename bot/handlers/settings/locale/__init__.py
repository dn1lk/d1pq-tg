from aiogram import Router


def setup(router: Router):
    from .main import router as main_rt

    sub_routers = (
        main_rt,
    )

    for sub_router in sub_routers:
        router.include_router(sub_router)
