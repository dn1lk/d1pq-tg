from functools import lru_cache
from random import choice

import markovify

from bot import config


def set_data(text: str, messages: list | None = None) -> list | None:
    if messages == ['decline']:
        return
    elif not messages:
        messages = []

    sentences = [
        sentence for sentence in markovify.split_into_sentences(text) if
        len(sentence.split()) > 1 and sentence not in messages
    ]

    if sentences:
        messages.extend(sentences)

        if len(messages) > 5000:
            messages = messages[1000:]

        return messages


books = ('galaxy', 'war-and-peace', 'war-worlds')


@lru_cache(maxsize=4)
def get_base(locale: str, book: str, state_size: int = 1) -> markovify.Text:
    with open(
            config.BASE_DIR / 'locales' / locale / f'{book}.txt',
            'r',
            encoding='UTF-8'
    ) as f:
        return markovify.Text(f.read(), state_size=state_size)


@lru_cache(maxsize=2)
def get_none(locale: str) -> markovify.Text:
    with open(
            config.BASE_DIR / 'locales' / locale / 'none.txt',
            'r',
            encoding='UTF-8'
    ) as f:
        return markovify.Text(f.read(), retain_original=False)


def gen(
        locale: str,
        messages: list | None = None,
        text: str = None,
        state_size: int = 2,
        tries: int = 250,
        min_words: int = None,
        max_words: int = None,
) -> str:
    model = get_base(locale, choice(books), state_size=state_size)

    if messages:
        model_messages = markovify.Text(messages, state_size=state_size)

        if len(messages) > 50 * state_size:
            model = model_messages
        else:
            model = markovify.combine(
                models=(model_messages, model),
                weights=(100, 0.01)
            )

    try:
        if text:
            answer = model.make_sentence_with_start(
                beginning=choice(text.split()),
                strict=False,
                tries=state_size * tries,
                min_words=min_words,
                max_words=max_words,
            )

            if not answer:
                raise markovify.text.ParamError("`make_sentence_with_start` didn't have an answer")
        else:
            raise markovify.text.ParamError(
                f"`make_sentence_with_start` for this model requires a string "
                f"containing 1 to {state_size} words. "
                f"Yours has 0 words"
            )
    except (markovify.text.ParamError, LookupError, TypeError):
        answer = model.make_sentence(
            tries=state_size * tries,
            min_words=min_words,
            max_words=max_words,
        )

    return answer or get_none(locale).make_sentence()
