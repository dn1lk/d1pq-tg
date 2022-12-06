from aiohttp import ClientSession

from aiogram.utils.i18n import gettext as _


class Wikipedia:
    session = ClientSession()

    async def gen(self, locale: str, title: str):
        async with self.session.get(f'https://{locale}.wikipedia.org/w/api.php?format=json&action=query&prop=extracts&exsentences=2&exintro&explaintext&redirects=1&titles={title}') as resp:
            answer = await resp.json()

        try:
            return _("In short, — ") + \
                   list(answer['query']['pages'].values())[0]['extract'].split(' — ')[1].split('. ')[0]
        except KeyError:
            return _("I don't know answer =(")
