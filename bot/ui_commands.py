from aiogram import Bot, types
from aiogram.utils.i18n import I18n

from handlers import Commands


async def get_my_commands(bot: Bot, i18n: I18n, locale: str) -> tuple[types.BotCommand]:
    async def set_my_commands(*exclude_commands, scope: types.BotCommandScope):
        await bot.set_my_commands(
            commands=(
                [command for command in commands if command.command not in exclude_commands]
                if exclude_commands
                else list(commands)
            ),
            scope=scope,
            language_code=locale
        )

    with i18n.context(), i18n.use_locale(locale):
        commands: tuple[types.BotCommand] = tuple(Commands.iter())

    if locale == 'en':
        locale = None

    await set_my_commands(Commands.WHO.value[0],
                          scope=types.BotCommandScopeAllPrivateChats())
    await set_my_commands(scope=types.BotCommandScopeAllChatAdministrators())
    await set_my_commands(Commands.SETTINGS.value[0],
                          scope=types.BotCommandScopeAllGroupChats())

    return commands


async def setup(bot: Bot, i18n: I18n) -> dict[str, tuple[types.BotCommand]]:
    return {locale: await get_my_commands(bot, i18n, locale) for locale in i18n.available_locales}
