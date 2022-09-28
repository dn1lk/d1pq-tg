from aiohttp import ClientSession, ClientResponseError

from .markov import get_none


class Yalm:
    __slots__ = ("session", "intros")

    def __init__(self):
        self.session = ClientSession()
        self.intros: dict[str, tuple] = {}

    async def gen(self, locale: str, query: str, intro: int | None = 0) -> str:
        try:
            answer = await self._get_response(
                method="POST",
                endpoint="text3",
                json={
                    "query": query,
                    "intro": intro if locale == "ru" else self.intros['en'][self.intros['ru'].index(intro)],
                    "filter": 1
                }
            )

            if intro in (3, 6, 8, 11) or len(answer["query"]) < 10 and len(answer["answers"]) < 20:
                return answer["query"] + answer["text"]
            else:
                return answer["text"]
        except ClientResponseError:
            return get_none(locale).make_sentence()

    async def setup(self):
        for locale in ("ru", "en"):
            endpoint = "intros" if locale == "ru" else "intros_eng"
            response = await self._get_response(method="GET", endpoint=endpoint)
            self.intros[locale] = tuple(intro[0] for intro in response["intros"])

        return self

    async def _get_response(
        self,
        *,
        method: str,
        endpoint: str,
        json: dict | None = None,
    ):
        if not self.session or self.session.closed:
            self.session = ClientSession()

        return await self._fetch(
            method=method,
            endpoint=endpoint,
            json=json,
        )

    async def _fetch(
            self,
            method: str,
            endpoint: str,
            json: dict,
    ):
        async with self.session.request(
            method,
            f"https://yandex.ru/lab/api/yalm/{endpoint}",
            json=json,
            raise_for_status=True,
        ) as response:
            return await response.json()
