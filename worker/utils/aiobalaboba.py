from typing import Optional

from aiohttp import ClientSession, ContentTypeError

from markov import get_none_data


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
    except (ContentTypeError, LookupError):
        return get_none_data().make_sentence()
