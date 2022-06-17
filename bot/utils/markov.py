from json import load
from random import choice

import markovify

from bot import config


def set_data(text: str, messages: list | None = None) -> list | None:
    if not messages:
        messages = []
    elif ['DECLINE'] == messages:
        return

    sentences = [
        sentence for sentence in markovify.split_into_sentences(text) if
        len(sentence.split()) > 1 and sentence not in messages
    ]

    if sentences:
        if messages:
            messages += sentences

            if len(messages) > 5000:
                messages = messages[1000:]
        else:
            messages = sentences

        return messages


def get_base(locale: str, state_size: int | None = 1):
    with open(
            config.BASE_DIR / 'locales' / locale / 'war-and-peace.json',
            'r',
            encoding='UTF-8'
    ) as f:
        return markovify.Text(
            None,
            parsed_sentences=load(f)[::choice(range(1, int(10 / state_size)))],
            state_size=state_size
        )


def get_none(locale: str):
    with open(
            config.BASE_DIR / 'locales' / locale / 'none.json',
            'r',
            encoding='UTF-8'
    ) as f:
        return markovify.Text(None, parsed_sentences=load(f), retain_original=False)


async def gen(
        locale: str,
        messages: str | list | None = None,
        text: str | None = None,
        state_size: int = 2,
        min_words: int | None = None,
        max_words: int = 20,
) -> str:
    model = get_base(locale, state_size)

    if messages:
        model_messages = markovify.Text(
                    None,
                    parsed_sentences=[message.split() for message in messages],
                    state_size=state_size
                )

        if len(messages) > 100:
            model = model_messages
        else:
            model = markovify.combine(
                models=(
                    model_messages,
                    model
                ),
                weights=(100, 0.01)
            )

    model.compile(inplace=True)

    try:
        if text:
            answer = model.make_sentence_with_start(
                beginning=choice(text.split()),
                strict=False,
                tries=state_size * 10,
                min_words=min_words,
                max_words=max_words,
            )
        else:
            err_msg = (
                f"`make_sentence_with_start` for this model requires a string "
                f"containing 1 to {state_size} words. "
                f"Yours has 0 words"
            )
            raise markovify.text.ParamError(err_msg)
    except (markovify.text.ParamError, LookupError, TypeError):
        answer = model.make_sentence(tries=state_size * 10, min_words=min_words, max_words=max_words)

    return answer or get_none(locale).make_sentence()
