from random import choice
from re import Match, sub

from aiogram.utils.i18n import I18n


def resolve_text(text: str) -> str:
    def cap(match: Match):
        return match.group().capitalize()

    text = sub(r'^\w+|(?<=[.?!]\s)\w+', cap, text.strip())

    if text[-1] in ':-,':
        text = text[:-1] + '.'
    elif text[-1] not in '.!?()':
        text += '.'

    return text


def messages_to_words(i18n: I18n, messages: list[str]) -> list[str]:
    if messages and len(messages) > 1:
        return sum((sentence.split() for sentence in messages), [])
    else:
        from bot.utils import markov
        return sum(markov.get_base(i18n.current_locale, choice(markov.BOOKS)).parsed_sentences, [])
