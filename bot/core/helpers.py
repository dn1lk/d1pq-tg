import functools
import operator
import re

from aiogram import types

_re_blockcode = re.compile(r"(?<!\\)(\`{3}).+?(?<!\\)(\1)", flags=re.DOTALL)
_re_formatted = re.compile(_re_blockcode.pattern + r"|(?<!\\)([\*\_\`])[^\n]+?(?<!\\)(\3)", flags=re.DOTALL)
_re_escape = re.compile(r"(?<!\\)([\*\_\`\[\]\(\)\~\>\#\+\-\=\|\{\}\.\!])")

_re_sentence = re.compile(
    _re_blockcode.pattern
    + r"|(?:^|(?<=[\n\.\?\!][\ \t\v]|\\n))(?:(?!\\n)[^\n\.\?\!]){8,}?(?:$|[\n\.\?\!]+?|(?=(?:\\n)+))",
    flags=re.MULTILINE | re.DOTALL,
)


def resolve_text(text: str, *, escape: bool = False) -> str:
    def fix_secuence(match: re.Match) -> str:
        t: str = match.group(0)
        if _re_blockcode.match(t):  # code sequence
            return t

        t = t.strip()
        t = t.capitalize()

        if t[-1] in ":-,":
            t = t[:-1] + "."
        elif t[-1] not in ".!?":
            t += "."

        return t

    text = _re_sentence.sub(fix_secuence, text)

    if escape:
        text_escaped = ""
        end = 0
        for match in _re_formatted.finditer(text):
            if match.group(1):
                i1 = 1
                i2 = 2
            else:
                i1 = 3
                i2 = 4

            text_escaped += _re_escape.sub(r"\\\1", text[end : match.start(i1)])
            text_escaped += match.group(i1)
            text_escaped += _re_escape.sub(r"\\\1", text[match.end(i1) : match.start(i2)])
            text_escaped += match.group(i2)

            end = match.end(i2)

        text_escaped += _re_escape.sub(r"\\\1", text[end:])
        text = text_escaped

    return text


def get_text(message: types.Message) -> str:
    return message.text or message.caption or (message.poll.question if message.poll else "")


def get_split_text(messages: list[str]) -> list[str]:
    return functools.reduce(operator.iadd, (message.split() for message in messages), [])
