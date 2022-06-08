from typing import Optional, Union, Dict, Any

from aiogram import types, Bot
from aiogram.dispatcher import filters


class CustomCommandFilter(filters.Command):
    async def __call__(
            self,
            message: types.Message,
            bot: Bot,
            custom_commands: Optional[dict] = None
    ) -> Union[bool, Dict[str, Any]]:
        if custom_commands and custom_commands.get(self.commands[0]):
            self.commands.append(custom_commands[self.commands[0]])

        return await super().__call__(message, bot)
