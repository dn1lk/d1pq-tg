from re import Match, sub

from aiogram import types


def resolve_text(text: str) -> str:
    def cap(match: Match):
        return match.group().capitalize()

    text = sub(r'^\w+|(?<=[.?!]\s)\w+', cap, text.strip())

    if text[-1] in ':-,':
        text = text[:-1] + '.'
    elif text[-1] not in '.!?()':
        text += '.'

    return text


def get_text(message: types.Message):
    return message.text or message.caption or (message.poll.question if message.poll else "")


def get_split_text(messages: list[str]) -> list[str]:
    return sum((message.split() for message in messages), [])
