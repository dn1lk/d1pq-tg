from functools import lru_cache
from random import choice

from bot import config
from ... import GamesData


@lru_cache(maxsize=2)
def get_cities(locale: str) -> list:
    with open(config.BASE_DIR / 'locales' / locale / 'cities.txt', 'r', encoding='utf8') as r:
        return r.read().splitlines()


class CTSData(GamesData):
    bot_var: str = None
    cities: list[str] = []
    fail_amount: int = 5

    @classmethod
    def filter(cls):
        from .filter import CTSFilter
        return CTSFilter()

    def gen_var(self, user_var: str, game_vars: list[str]) -> None:
        def gen_city():
            for city in game_vars:
                if city[0].lower() == user_var[-1].lower() and city not in self.cities:
                    yield city
            yield None

        self.bot_var = choice(tuple(gen_city()))
        if self.bot_var:
            self.cities.append(self.bot_var)
