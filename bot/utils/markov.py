from functools import lru_cache
from os import listdir
from random import choice, shuffle, randrange

import markovify

from bot import config

LOCALE_DIR = config.BASE_DIR / 'locales'
BOOKS = listdir(LOCALE_DIR / 'en' / 'books')


def set_data(text: str | None, messages: list | None) -> list:
    if messages == ['disabled']:
        return messages
    elif not messages:
        messages = []

    if text:
        messages += markovify.split_into_sentences(text)

        if len(messages) > 5000:
            messages = messages[1000:]

    return messages


@lru_cache(maxsize=4)
def get_base(locale: str, book: str, state_size: int = 1) -> markovify.Text:
    with open(
            LOCALE_DIR / locale / 'books' / book,
            mode='r',
            encoding='UTF-8'
    ) as f:
        return markovify.Text(f.read(), state_size=state_size)


@lru_cache(maxsize=2)
def get_none(locale: str) -> markovify.Text:
    with open(
            LOCALE_DIR / locale / 'none.txt',
            mode='r',
            encoding='UTF-8'
    ) as f:
        return markovify.Text(f.read(), retain_original=False)


def gen(
        locale: str,
        messages: list[str] | None = None,
        text: str = '',
        state_size: int = 2,
        tries: int = 500,
        **kwargs,
) -> str:
    max_words = kwargs.pop("max_words", randrange(2, state_size * 2))

    if messages:
        model = markovify.Text(messages, state_size=state_size, well_formed=False)

        if len(messages) < 50 * state_size:
            base_model = get_base(locale, choice(BOOKS), state_size=state_size)
            model = markovify.combine((base_model, model),
                                      weights=(0.01, 1))
    else:
        model = get_base(locale, choice(BOOKS), state_size=state_size)

    def get_states(run: list):
        items = ([markovify.chain.BEGIN] * state_size) + run + [markovify.chain.END]

        for i in range(1, len(run) + 1):
            yield items[i: i + model.state_size]

    def make_sentence(init_state: tuple = None):
        return model.make_sentence(init_state=init_state,
                                   tries=state_size * tries,
                                   max_words=max_words,
                                   **kwargs)

    sentences = model.parsed_sentences.copy()
    shuffle(sentences)

    for sentence in sentences:
        if any(word in sentence for word in text.split()):
            states = list(get_states(model.parsed_sentences[model.parsed_sentences.index(sentence) + 1]))

            for state in states:
                answer = make_sentence(tuple(state))

                if answer:
                    return answer

            max_words += 1

    return make_sentence() or get_none(locale).make_sentence()
