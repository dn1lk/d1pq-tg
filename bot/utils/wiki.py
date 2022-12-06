from re import split

from aiohttp import ClientSession

from aiogram.utils.i18n import gettext as _

from . import markov


class Wikipedia:
    session = ClientSession()

    async def gen(self, locale: str, title: str):
        async with self.session.get(f'https://{locale}.wikipedia.org/w/api.php?format=json&action=query&prop=extracts&explaintext&exsentences=5&redirects=1&titles={title}') as resp:
            answer = await resp.json()

        try:
            return _("In short, ") + markov.gen(
                locale,
                messages=list(answer['query']['pages'].values())[0]['extract'],
                text=title,
                test_output=False,
                max_words=50,
            )
        except KeyError:
            return _("I don't know answer =(")
