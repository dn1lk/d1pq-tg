from aiogram import Router


def setup(parent_router: Router):
    from .start import router as start_rt
    from .update import router as process_rt

    parent_router.include_routers(
        process_rt,
        start_rt,
    )
