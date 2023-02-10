from enum import Enum
from random import choice
from re import sub

from aiogram import Router, types
from aiogram.utils.i18n import I18n, gettext as _


def answer_check(answer: str) -> str:
    def cap(match):
        return match.group().capitalize()

    answer = sub(r'((?<=[.?!]\s)(\w+)|(^\w+))', cap, answer.strip())

    if answer[-1] in ':-,':
        answer = answer[:-1] + '.'
    elif answer[-1] not in '.!?()':
        answer += '.'

    return answer


def commands_to_str(ui_commands: tuple[types.BotCommand]) -> str:
    return '\n'.join(f'/{command.command} - {command.description}' for command in ui_commands)


def messages_to_words(i18n: I18n, messages: list[str]) -> list[str]:
    if messages and len(messages) > 1:
        return sum((sentence.split() for sentence in messages), [])
    else:
        from ..utils import markov
        return sum(markov.get_base(i18n.current_locale, choice(markov.BOOKS)).parsed_sentences, [])


class Commands(Enum):
    SETTINGS = 'settings', 'настройки'
    HELP = 'help', 'помощь'
    TERMS = 'terms', 'условия'

    CHOOSE = 'choose', 'выбери'
    WHO = 'who', 'кто'
    PLAY = 'play', 'поиграем'
    QUESTION = 'question', 'вопросик'
    HISTORY = 'history', 'короче'
    FUTURE = 'future', 'погадай'

    START = 'start', 'начать'

    @property
    def description(self):
        match self:
            case self.SETTINGS:
                return _("set up the bot")
            case self.HELP:
                return _("get a commands list")
            case self.TERMS:
                return _("get using terms")

            case self.CHOOSE:
                return _("make a choice")
            case self.WHO:
                return _("find the desired participant")
            case self.PLAY:
                return _("play in a game")
            case self.QUESTION:
                return _("answer the question")
            case self.HISTORY:
                return _("tell a story")
            case self.FUTURE:
                return _("predict the future")

    @classmethod
    def iter(cls):
        for command in cls:
            if command.description:
                yield types.BotCommand(command=command.value[0],
                                       description=command.description)


def setup(router: Router):
    '''    from .games import setup as game_st
        from .settings import setup as setting_st
        from .transitions import setup as transitions_st

        game_st(router)
    '''
    from .choose import router as choose_rt
    from .error import router as error_rt
    from .help import router as help_rt
    from .history import router as history_rt
    from .other import router as other_rt
    from .question import router as question_rt
    from .start import router as start_rt
    from .who import router as who_rt

    sub_routers = (
        question_rt,
        choose_rt,
        who_rt,
        history_rt,
        help_rt,
        start_rt,
        other_rt,
        error_rt,
    )

    for sub_router in sub_routers:
        router.include_router(sub_router)
