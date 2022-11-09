from functools import lru_cache
from os import listdir
from random import choice

import markovify


def set_data(text: str, messages: list | None) -> list:
    if messages == ['disabled']:
        return []
    elif not messages:
        messages = []

    sentences = markovify.split_into_sentences(text)

    if sentences:
        messages = list(set(messages + sentences))

        if len(messages) > 5000:
            messages = messages[1000:]

    return messages


books = listdir('bot/locales/en/books')


@lru_cache(maxsize=4)
def get_base(locale: str, book: str, state_size: int = 1) -> markovify.Text:
    from bot import config

    with open(
            config.BASE_DIR / 'locales' / locale / 'books' / book,
            mode='r',
            encoding='UTF-8'
    ) as f:
        return markovify.Text(f.read(), state_size=state_size)


@lru_cache(maxsize=2)
def get_none(locale: str) -> markovify.Text:
    from bot import config

    with open(
            config.BASE_DIR / 'locales' / locale / 'none.txt',
            mode='r',
            encoding='UTF-8'
    ) as f:
        return markovify.Text(f.read(), retain_original=False)


def gen(
        locale: str,
        messages: list[str] | None = None,
        text: str = None,
        state_size: int = 2,
        tries: int = 500,
        **kwargs,
) -> str:
    model = get_base(locale, choice(books), state_size=state_size)

    if messages:
        model_messages = markovify.Text(messages, state_size=state_size)

        if len(messages) > 50 * state_size:
            model = model_messages
        else:
            model = markovify.combine(models=(model_messages, model), weights=(100, 0.01))

    try:
        beginning = choice(text.split())

        answer: str | None = model.make_sentence_with_start(
            beginning=beginning,
            strict=False,
            tries=state_size * tries,
            **kwargs,
        )

        if not answer:
            raise markov.text.ParamError("No answer with 'make_sentence_with_start'")

        answer = answer.replace(f'{beginning} ', '', 1)
    except:
        answer = model.make_sentence(tries=state_size * tries, **kwargs)

    return answer or get_none(locale).make_sentence()
