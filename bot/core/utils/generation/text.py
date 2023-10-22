from functools import lru_cache
from random import randrange, shuffle

import markovify
from Levenshtein import ratio

import misc
from core.utils import database

LOCALE_DIR = f'{misc.BASE_DIR}/core/locales'


@lru_cache(maxsize=2)
def __get_none(locale: str) -> markovify.Text:
    with open(
            f'{LOCALE_DIR}/{locale}/none.txt',
            mode='r',
            encoding='UTF-8'
    ) as f:
        return markovify.Text(f.read(), retain_original=False)


def __make_sentence(model: markovify.Text, accuracy: int, tries: int = 10, **kwargs) -> str | None:
    return model.make_sentence(tries=accuracy * tries, **kwargs)


def __get_states(model: markovify.Text, accuracy: int, index: int):
    run = model.parsed_sentences[index]

    items = ([markovify.chain.BEGIN] * accuracy) + run + [markovify.chain.END]

    for i in range(1, len(run) + 1):
        yield items[i: i + model.state_size]


def get_answer(
        text: str,
        gen_settings: database.GenSettings,
        **kwargs
) -> str:
    if gen_settings.messages:
        kwargs.setdefault("test_output", False)
        kwargs.setdefault("max_words", randrange(2, gen_settings.accuracy * 6))

        model = markovify.Text(gen_settings.messages, state_size=gen_settings.accuracy, well_formed=False)

        words = set(text.split())

        sentences = model.parsed_sentences.copy()
        shuffle(sentences)

        for sentence in sentences:
            if any(ratio(s, w) > 0.9 for s in set(sentence) for w in words):
                index = (model.parsed_sentences.index(sentence) + 1) % len(model.parsed_sentences)

                for init_state in __get_states(model, gen_settings.accuracy, index):
                    answer = __make_sentence(model, gen_settings.accuracy, init_state=tuple(init_state), **kwargs)
                    if answer:
                        return answer

        answer = __make_sentence(model, gen_settings.accuracy, **kwargs)
        if answer:
            return answer

    return __get_none(misc.i18n.current_locale).make_sentence()
