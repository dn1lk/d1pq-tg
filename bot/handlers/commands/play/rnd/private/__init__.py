from aiogram import Router, F, enums

router = Router(name='play:rnd:private')


def setup(parent_router: Router):
    router.message.filter(F.chat.type == enums.ChatType.PRIVATE)

    parent_router.include_router(router)

    from . import process, start
    router.include_routers(
        process.router,
        start.router
    )
