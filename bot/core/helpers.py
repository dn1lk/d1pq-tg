import functools
import operator
import re

from aiogram import types


def resolve_text(text: str, *, screen: bool = False) -> str:
    text = re.sub(r"^\w+|(?<=[.?!]\s)\w+", lambda m: m.group().capitalize(), text.strip())

    if text[-1] in ":-,":
        text = text[:-1] + "."
    elif text[-1] not in "`.!?()":
        text += "."

    if screen:
        text = re.sub(r"(?<!\\)(\[|\]|\(|\)|\~|>|#|\+|-|=|\||\{|\}|\.|\!)", lambda m: "\\" + m.group(), text)

    return text


def get_text(message: types.Message) -> str:
    return message.text or message.caption or (message.poll.question if message.poll else "")


def get_split_text(messages: list[str]) -> list[str]:
    return functools.reduce(operator.iadd, (message.split() for message in messages), [])
