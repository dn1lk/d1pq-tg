from typing import Optional, Union, Dict, Any

from aiogram import Bot, types, filters


class CustomCommandFilter(filters.Command):
    async def __call__(
            self,
            message: types.Message,
            bot: Bot,
            custom_commands: Optional[dict[str, tuple]] = None
    ) -> Union[bool, Dict[str, Any]]:
        if custom_commands and self.commands[0] in custom_commands:
            self.commands = (*self.commands, custom_commands[self.commands[0]])

        return await super().__call__(message, bot)
