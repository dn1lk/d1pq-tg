from enum import Enum, EnumMeta

from aiogram.utils.i18n import gettext as _

PREFIX = "/"


class CommandTypesMeta(EnumMeta):
    @property
    def start_commands(cls) -> list["CommandTypesMeta"]:
        return list(cls)[:3]

    @property
    def help_commands(cls) -> list["CommandTypesMeta"]:
        return list(cls)[3:-1]


class CommandTypes(tuple, Enum, metaclass=CommandTypesMeta):
    __slots__ = ()

    SETTINGS = "settings", "настройки"
    HELP = "help", "помощь"
    TERMS = "terms", "условия"

    CHOOSE = "choose", "выбери"
    WHO = "who", "кто"
    PLAY = "play", "поиграем"

    START = "start", "начать"

    def __str__(self) -> str:
        return f"{PREFIX}{self[0]} — {self.description}"

    @property
    def description(self) -> str | None:
        match self:
            case self.SETTINGS:
                description = _("set up the bot")
            case self.HELP:
                description = _("get a commands list")
            case self.TERMS:
                description = _("get users terms")

            case self.CHOOSE:
                description = _("make a choice")
            case self.WHO:
                description = _("find the desired participant")
            case self.PLAY:
                description = _("play in a game")
            case self.START:
                description = None
            case _:
                msg = f"Unknown command: {self}"
                raise TypeError(msg)

        return description
