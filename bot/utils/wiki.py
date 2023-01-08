from aiogram.utils.i18n import gettext as _
from aiohttp import ClientSession

from . import markov


class Wikipedia:
    session = ClientSession()
    url = 'https://{locale}.wikipedia.org/w/api.php?' \
          'format=json&' \
          'action=query&' \
          'prop=extracts&' \
          'explaintext&' \
          'exsentences=5&' \
          'redirects=1&' \
          'titles={titles}'

    async def gen(self, locale: str, titles: str):
        async with self.session.get(self.url.format(locale=locale, titles=titles)) as resp:
            answer = await resp.json()

        try:
            return _("In short, ") + markov.gen(
                locale,
                messages=list(answer['query']['pages'].values())[0]['extract'],
                text=set(titles.split()),
                test_output=False,
                max_words=25,
                min_words=5,
            )
        except KeyError:
            return _("I don't know answer =(")
