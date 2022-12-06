from aiohttp import ClientSession, ClientResponse


class Yalm:
    intros: dict[str, tuple] = {}

    def __init__(self, session: ClientSession):
        self.session = session

    async def _get_resp(self, method: str, endpoint: str, json: dict = None):
        async with self.session.request(method=method, url=f'/lab/api/yalm/{endpoint}', json=json) as resp:
            if resp.ok:
                return await resp.json(content_type='text/html')

    @classmethod
    async def setup(cls) -> "Yalm":
        yalm = cls(session=ClientSession('https://yandex.ru'))
        locales = {
            'ru': 'intros',
            'en': 'intros_eng',
        }

        for locale, intro in locales.items():
            resp = await yalm._get_resp('GET', intro)
            yalm.intros[locale] = tuple(intro[0] for intro in resp["intros"])

        return yalm

    async def close(self):
        await self.session.close()

    async def gen(self, locale: str, query: str, intro: int | None = 0) -> str:
        resp = await self._get_resp('POST', 'text3', json={
                    "query": query,
                    "intro": intro if locale == "ru" else self.intros['en'][self.intros['ru'].index(intro)],
                    "filter": 1
                }
        )

        if not resp:
            from .markov import get_none
            return get_none(locale).make_sentence()

        if intro in (3, 6, 8, 11) or len(resp["query"]) < 10 and len(resp["text"]) < 20:
            return resp["query"] + resp["text"]
        else:
            return resp["text"]
