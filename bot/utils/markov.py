import os
from functools import lru_cache
from pathlib import Path
from random import choice, shuffle, randrange

import markovify

from . import database

LOCALE_DIR = Path.cwd() / 'bot' / 'locales'
BOOKS = os.listdir(f'{LOCALE_DIR}/en/books')


async def set_messages(db: database.SQLContext, text: str, chat_id: int, messages: list[str] = None):
    messages: list[str] = messages or await db.messages.get(chat_id) or []

    if messages != ['disabled']:
        text = markovify.split_into_sentences(text)

        if len(messages) > 5000:
            messages = messages[1000:] + text
            await db.messages.set(chat_id, messages)
        else:
            messages = await db.messages.cat(chat_id, text)
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
        text: str,
        messages: list[str],
        state_size: int = 2,
        **kwargs,
) -> str:
    kwargs.setdefault("max_words", randrange(1, state_size * 2))

    if messages:
        model = markovify.Text(messages, state_size=state_size, well_formed=False)

        if len(messages) < 50 * state_size:
            base_model = get_base(locale, choice(BOOKS), state_size=state_size)
            model = markovify.combine((base_model, model), weights=(0.01, 1))
    else:
        model = get_base(locale, choice(BOOKS), state_size=state_size)

    def get_states(run: list[str]):
        items = ([markovify.chain.BEGIN] * state_size) + run + [markovify.chain.END]

        for i in range(1, len(run) + 1):
            yield items[i: i + model.state_size]

    def make_sentence(init_state: tuple[str] = None):
        return model.make_sentence(init_state=init_state, **kwargs)

    sentences = model.parsed_sentences.copy()
    shuffle(sentences)

    if text:
        text = set(text.split())

        for sentence in sentences:
            if text & set(sentence):
                index = (model.parsed_sentences.index(sentence) + 1) % len(model.parsed_sentences)
                for state in get_states(model.parsed_sentences[index]):
                    answer = make_sentence(tuple(state))

                    if answer:
                        return answer

    return make_sentence() or get_none(locale).make_sentence()
