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


async def set_bot_commands(bot: Bot, dp: Dispatcher) -> dict:
    commands_dict = {}

    for locale in config.i18n.available_locales:
        commands_dict[locale] = list(get_bot_commands(dp, locale))

        data = (
            (
                list(filter(lambda command: command.command != 'settings', commands_dict[locale])),
                BotCommandScopeDefault()
            ),
            (
                commands_dict[locale],
                BotCommandScopeAllChatAdministrators(),
            ),
            (
                list(filter(lambda command: command.command != 'who', commands_dict[locale])),
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
