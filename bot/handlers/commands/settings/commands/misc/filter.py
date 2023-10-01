from aiogram import Bot, filters, types

from core.utils import database
from handlers.commands.misc.types import PREFIX


class CustomCommand(filters.Command):
    def __init__(self, *values, with_customs: bool = True, **kwargs):
        super().__init__(*values, **kwargs)
        self.prefix = PREFIX
        self.with_customs = with_customs

    async def __call__(
            self, message: types.Message, bot: Bot,
            main_settings: database.MainSettings = None,
    ):
        if self.with_customs:
            commands = main_settings.commands.get(self.commands[0])

            if commands:
                self.commands += commands,

        return await super().__call__(message, bot)
