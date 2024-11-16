import random as rnd
import secrets
from functools import lru_cache
from pathlib import Path

import markovify
from aiogram.utils.i18n import I18n
from Levenshtein import ratio

import config
from utils import database

ALIGN_RATIO = 0.9


@lru_cache(maxsize=2)
def _get_none(locale: str) -> markovify.Text:
    with Path(f"{config.LOCALE_PATH}/{locale}/none.txt").open(encoding="UTF-8") as f:
        return markovify.Text(f.read(), retain_original=False)


def _get_states(model: markovify.Text, accuracy: int, index: int):
    run = model.parsed_sentences[index]

    items = ([markovify.chain.BEGIN] * accuracy) + run + [markovify.chain.END]

    for i in range(1, len(run) + 1):
        yield items[i : i + model.state_size]


def _make_sentence(model: markovify.Text, accuracy: int, tries: int = 10, **kwargs) -> str | None:
    return model.make_sentence(tries=accuracy * tries, **kwargs)


def get_answer(text: str, i18n: I18n, gen_settings: database.GenSettings, **kwargs) -> str:
    if gen_settings.messages:
        kwargs.setdefault("test_output", False)
        kwargs.setdefault("max_words", secrets.randbelow(gen_settings.accuracy * 4) + 2)

        model = markovify.Text(gen_settings.messages, state_size=gen_settings.accuracy, well_formed=False)

        words = set(text.split())

        sentences = model.parsed_sentences.copy()
        rnd.shuffle(sentences)

        for sentence in sentences:
            if any(ratio(s, w) > ALIGN_RATIO for s in set(sentence) for w in words):
                index = (model.parsed_sentences.index(sentence) + 1) % len(model.parsed_sentences)

                for init_state in _get_states(model, gen_settings.accuracy, index):
                    answer = _make_sentence(model, gen_settings.accuracy, init_state=tuple(init_state), **kwargs)
                    if answer:
                        return answer

        answer = _make_sentence(model, gen_settings.accuracy, **kwargs)
        if answer:
            return answer

    return _get_none(i18n.current_locale).make_sentence()
