from typing import Optional

import markovify
from aiogram.utils.i18n import gettext as _
from aiohttp import ClientSession, ContentTypeError


async def fetch(query: str, intro: int, session: ClientSession) -> str:
    async with session.post(
            "https://yandex.ru/lab/api/yalm/text3",
            json={"query": query, "intro": intro, "filter": 1},
    ) as resp:
        r = await resp.json()
    if intro in (3, 6, 8, 11) or len(r["query"]) < 10 and len(r["answers"]) < 20:
        return r["query"] + r["answers"]
    else:
        return r["answers"]


async def get(query: str, intro: Optional[int] = 0) -> str:
    try:
        async with ClientSession(trust_env=True) as session:
            return await fetch(query, intro=intro, session=session)
    except LookupError:
        return markovify.Text(
            [
                _("I think I wanted to write something, but I don't remember what... x)."),
                _("I had some request... but I can't remember which one..."),
                _("I still can't remember... who are you?"),
                _("What do you want from me?"),
                _("What a wonderful day for doing nothing!"),
                _("Zzzz... What?"),
                _("Zzzz... I'm sleeping."),
                _("Zzzz... ZZZzz... ZzzZz..."),
            ],
            retain_original=False
        ).make_sentence()
    except ContentTypeError:
        return markovify.Text(
            [
                _("I feel dark energy. Now it's better not to write anything..."),
                _("Evil forces took away my mind, now I can only write about the fact that I can’t do anything..."),
                _("Coldly. Possible precipitation in the form of errors on the server. Carefully."),
                _("Today I will have a day off from all of you!"),
                _("I'm waiting for an answer..."),
                _("The wait is over."),
                _("So-ooo, goodbye!"),
                _("I was limited in functionality =(."),
            ],
            retain_original=False
        ).make_sentence()
