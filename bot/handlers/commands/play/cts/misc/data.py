from functools import lru_cache
from pathlib import Path
from random import choice

from ... import PlayData

LOCALE_DIR = Path.cwd() / 'bot' / 'core' / 'locales'


class CTSData(PlayData):
    bot_city: str = None
    used_cities: set[str] = set()
    fail_amount: int = 5

    @classmethod
    def filter(cls):
        from .filter import CTSFilter
        return CTSFilter()

    @classmethod
    @lru_cache(maxsize=2)
    def get_cities(cls, locale: str) -> list[str]:
        with open(LOCALE_DIR / locale / 'cities.txt', 'r', encoding='utf8') as r:
            return r.read().splitlines()

    def gen_city(self, cities: list[str], user_city: str = None) -> None:
        if user_city:
            bot_cities = [
                city for city in cities
                if city[0].lower() == user_city[-1].lower() and city not in self.used_cities
            ]
        else:
            bot_cities = cities

        self.bot_city = choice(bot_cities)

        if self.bot_city:
            self.used_cities.add(self.bot_city)
