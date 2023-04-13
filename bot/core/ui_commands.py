import logging

from aiogram import Bot, types
from aiogram.utils.i18n import I18n
from bot.handlers.commands import CommandTypes


async def setup(bot: Bot, i18n: I18n):
    logging.debug('Setting up ui_commands...')

    async def set_my_commands(*exclude_commands, scope: types.BotCommandScope = None):
        await bot.set_my_commands(
            commands=[command for command in my_commands if command not in exclude_commands],
            scope=scope,
            language_code=locale
        )

    for locale in i18n.available_locales:
        with i18n.context(), i18n.use_locale(locale):
            my_commands = [
                types.BotCommand(command=command[0], description=command.description)
                for command in CommandTypes
                if command.description
            ]

        if locale == 'en':
            locale = None

        await set_my_commands(CommandTypes.WHO,
                              scope=types.BotCommandScopeAllPrivateChats())
        await set_my_commands(scope=types.BotCommandScopeAllChatAdministrators())
        await set_my_commands(CommandTypes.SETTINGS,
                              scope=types.BotCommandScopeAllGroupChats())
