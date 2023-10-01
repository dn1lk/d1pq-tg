from aiogram import Router, F, enums

router = Router(name='rnd:private')
router.message.filter(F.chat.type == enums.ChatType.PRIVATE)


def setup(parent_router: Router):
    parent_router.include_router(router)

    from . import process, start
    router.include_routers(
        process.router,
        start.router
    )
