from aiogram import Router


def setup(parent_router: Router) -> None:
    from . import group, other, private

    parent_router.include_routers(
        group.router,
        private.router,
        other.router,
    )
