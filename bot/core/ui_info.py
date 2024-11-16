import logging

from aiogram import Bot, Dispatcher, types
from aiogram.utils.i18n import gettext as _

from handlers.commands import CommandTypes
from main import i18n

logger = logging.getLogger("bot")


async def set_my_commands(
    bot: Bot,
    locale: str | None,
    my_commands: list[types.BotCommand],
    *exclude_commands: CommandTypes,
    scope: (
        types.BotCommandScopeAllPrivateChats
        | types.BotCommandScopeAllChatAdministrators
        | types.BotCommandScopeAllGroupChats
        | None
    ) = None,
) -> None:
    await bot.set_my_commands(
        commands=[command for command in my_commands if command not in exclude_commands],
        scope=scope,
        language_code=locale,
    )


async def set_ui_info(bot: Bot) -> None:
    logger.debug("setting up ui_info...")

    for _locale in i18n.available_locales:
        locale = _locale

        with i18n.context(), i18n.use_locale(locale):
            my_commands = [
                types.BotCommand(command=command[0], description=command.description)
                for command in CommandTypes
                if command.description
            ]

            my_name = _("//delete")
            my_description = _(
                "Hello! I'm a text-generating bot based on your chat and a great conversationalist (sometimes).",
            )
            my_short_description = _("cha...{DELETED}-bot")

        if _locale == "en":
            locale = None

        await set_my_commands(
            bot,
            locale,
            my_commands,
            CommandTypes.WHO,
            scope=types.BotCommandScopeAllPrivateChats(),
        )
        await set_my_commands(
            bot,
            locale,
            my_commands,
            scope=types.BotCommandScopeAllChatAdministrators(),
        )
        await set_my_commands(
            bot,
            locale,
            my_commands,
            CommandTypes.SETTINGS,
            scope=types.BotCommandScopeAllGroupChats(),
        )

        await bot.set_my_name(my_name, language_code=locale)
        await bot.set_my_description(my_description, language_code=locale)
        await bot.set_my_short_description(my_short_description, language_code=locale)


def setup(dp: Dispatcher) -> None:
    dp.startup.register(set_ui_info)
