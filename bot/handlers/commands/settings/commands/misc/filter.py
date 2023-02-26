from aiogram import Bot, filters, types


class CustomCommand(filters.Command):
    async def __call__(
            self, message: types.Message, bot: Bot,
            commands: dict[str, list[str]] = None,
    ):
        if commands:
            commands = commands.get(self.commands[0])

            if commands:
                self.commands += commands,

        return await super().__call__(message, bot)
