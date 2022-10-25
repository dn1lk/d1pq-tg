from aiogram import Bot, Dispatcher, Router
from aiogram.types import (
    BotCommand,
    BotCommandScopeDefault,
    BotCommandScopeAllChatAdministrators,
    BotCommandScopeAllPrivateChats,
)

import config


def get_bot_commands(router: Router, locale: str):
    for handler in router.message.handlers:
        if "commands" in handler.flags and handler.callback.__doc__:
            for command in handler.flags["commands"]:
                yield BotCommand(
                    command=command.commands[0],
                    description=handler.callback.__doc__.split(', ')[config.i18n.available_locales.index(locale)]
                )

    for sub_router in router.sub_routers:
        yield from get_bot_commands(sub_router, locale)


async def set_bot_commands(bot: Bot, dp: Dispatcher) -> dict[str, tuple]:
    commands_dict = {}

    for locale in config.i18n.available_locales:
        commands_dict[locale] = tuple(get_bot_commands(dp, locale))

        data = (
            (
                [command for command in commands_dict[locale] if command.command != 'settings'],
                BotCommandScopeDefault()
            ),
            (
                commands_dict[locale],
                BotCommandScopeAllChatAdministrators(),
            ),
            (
                [command for command in commands_dict[locale] if command.command != 'who'],
                BotCommandScopeAllPrivateChats()
            ),
        )

        for commands, scope in data:
            await bot.set_my_commands(
                commands=commands,
                language_code=None if locale == 'en' else locale,
                scope=scope,
            )

    return commands_dict
