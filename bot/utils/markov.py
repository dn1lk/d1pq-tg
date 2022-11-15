from functools import lru_cache
from os import listdir
from random import choice, choices, shuffle

import markovify


def set_data(text: str | None, messages: list | None) -> list:
    if messages == ['disabled']:
        return []
    elif not messages:
        messages = []

    if text:
        sentences = markovify.split_into_sentences(text)
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

    if text:
        for t in text.lower().split():
            init_states = [key for key, value in model.chain.model.items() if t in (v.lower() for v in value)]
            shuffle(init_states)

            for init_state in init_states:
                answer = model.make_sentence(init_state=init_state, tries=state_size * tries, **kwargs)

                if answer:
                    return answer

    return model.make_sentence(tries=state_size * tries, **kwargs) or get_none(locale).make_sentence()
