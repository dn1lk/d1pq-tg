from enum import Enum

from aiogram.utils.i18n import gettext as _

PREFIX = '/'


class CommandTypes(tuple, Enum):
    SETTINGS = 'settings', 'настройки'
    HELP = 'help', 'помощь'
    TERMS = 'terms', 'условия'

    CHOOSE = 'choose', 'выбери'
    WHO = 'who', 'кто'
    PLAY = 'play', 'поиграем'
    QUESTION = 'question', 'вопросик'
    STORY = 'story', 'короче'

    START = 'start', 'начать'

    def __str__(self):
        return f"{PREFIX}{self[0]} — {self.description}"

    @property
    def description(self):
        match self:
            case self.SETTINGS:
                return _("set up the bot")
            case self.HELP:
                return _("get a commands list")
            case self.TERMS:
                return _("get users terms")

            case self.CHOOSE:
                return _("make a choice")
            case self.WHO:
                return _("find the desired participant")
            case self.PLAY:
                return _("play in a game")
            case self.QUESTION:
                return _("answer the question")
            case self.STORY:
                return _("tell a story")
