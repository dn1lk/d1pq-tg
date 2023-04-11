from aiogram import Bot, filters, types

from bot.handlers.commands.misc.types import PREFIX


class CustomCommand(filters.Command):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.prefix = PREFIX

    async def __call__(
            self, message: types.Message, bot: Bot,
            commands: dict[str, list[str]] = None,
    ):
        if commands:
            commands = commands.get(self.commands[0])

            if commands:
                self.commands += commands,

        return await super().__call__(message, bot)
