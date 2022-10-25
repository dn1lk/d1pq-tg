from functools import lru_cache
from os import listdir
from random import choice

import markovify

from bot import config


def set_data(text: str, messages: list | None = None) -> list | None:
    if messages == ['decline']:
        return
    elif not messages:
        messages = []

    sentences = set(markovify.split_into_sentences(text))

    if sentences:
        messages.extend(sentences)

        if len(messages) > 5000:
            messages = messages[1000:]

        return messages


books = listdir('bot/locales/en/books')


@lru_cache(maxsize=4)
def get_base(locale: str, book: str, state_size: int = 1) -> markovify.Text:
    with open(
            config.BASE_DIR / 'locales' / locale / 'books' / book,
            mode='r',
            encoding='UTF-8'
    ) as f:
        return markovify.Text(f.read(), state_size=state_size)


@lru_cache(maxsize=2)
def get_none(locale: str) -> markovify.Text:
    with open(
            config.BASE_DIR / 'locales' / locale / 'none.txt',
            mode='r',
            encoding='UTF-8'
    ) as f:
        return markovify.Text(f.read(), retain_original=False)


def gen(
        locale: str,
        messages: list | None = None,
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
        if text:
            answer = model.make_sentence_with_start(
                beginning=choice(text.split()),
                strict=False,
                tries=state_size * tries,
                **kwargs,
            )

            if not answer:
                raise markovify.text.ParamError("`make_sentence_with_start` didn't return an answer")
        else:
            raise markovify.text.ParamError(
                f"`make_sentence_with_start` for this model requires a string "
                f"containing 1 to {state_size} words. "
                f"Yours has 0 words"
            )
    except (markovify.text.ParamError, LookupError, TypeError):
        answer = model.make_sentence(tries=state_size * tries, **kwargs)

    return answer or get_none(locale).make_sentence()
