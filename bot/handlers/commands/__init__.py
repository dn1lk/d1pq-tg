from aiogram import Router

from .misc.types import CommandTypes

router = Router(name='commands')


def setup(parent_router: Router):
    from .settings.commands.misc.middleware import CustomCommandsMiddleware
    CustomCommandsMiddleware().setup(router)

    parent_router.include_router(router)

    from . import choose, help, question, start, story, who
    router.include_routers(
        choose.router,
        who.router,
        question.router,
        story.router,
        help.router,
        start.router,
    )

    from . import play, settings

    play.setup(router)
    settings.setup(router)
