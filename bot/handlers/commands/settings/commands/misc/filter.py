from typing import Any

from aiogram import Bot, filters, types

from handlers.commands.misc.types import PREFIX
from utils import database


class CustomCommand(filters.Command):
    def __init__(self, *values: filters.command.CommandPatternType, with_customs: bool = True, **kwargs):
        super().__init__(*values, **kwargs)
        self.prefix = PREFIX
        self.with_customs = with_customs

    async def __call__(
        self,
        message: types.Message,
        bot: Bot,
        main_settings: database.MainSettings | None = None,
    ) -> Any:
        if self.with_customs and main_settings.commands:
            commands = main_settings.commands.get(self.commands[0])

            if commands:
                self.commands += (commands,)

        return await super().__call__(message, bot)
