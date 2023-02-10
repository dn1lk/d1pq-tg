from aiogram import filters


class CustomCommand(filters.Command):
    async def __call__(self, custom_commands: dict[str, list] | None, **kwargs):
        if custom_commands:
            commands = custom_commands.get(self.commands[0])

            if commands:
                self.commands += tuple(commands)

        return await super().__call__(**kwargs)
