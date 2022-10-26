from functools import lru_cache
from random import choice

from pydantic import BaseModel

from bot import config, filters as f


@lru_cache(maxsize=2)
def get_cities(locale: str) -> list:
    with open(config.BASE_DIR / 'locales' / locale / 'cities.txt', 'r', encoding='utf8') as r:
        return r.read().splitlines()


class CtsData(BaseModel):
    bot_var: str = None
    cities: list[str] = []
    fail_amount: int = 5

    def filter_city(self, locale: str, user_var: str) -> bool | None:
        def filter_user_var():
            for game_var in game_vars:
                if game_var[0].lower() == user_var[0].lower():
                    yield f.LevenshteinFilter.lev_distance(game_var, user_var) <= max(len(game_var) / 5, 1)

        if not self.bot_var \
                or user_var[0].lower() == self.bot_var[-1].lower() \
                or user_var[0].lower() == self.bot_var[-2].lower() and self.bot_var[-1].lower() in ('ь', 'ъ'):
            if user_var not in self.cities:
                game_vars = get_cities(locale)

                if any(filter_user_var()):
                    self.cities.append(user_var)
                    self.gen_bot_var(user_var, game_vars)
                    return True

    def gen_bot_var(self, user_var: str, game_vars: list[str]) -> None:
        def get_city():
            for city in game_vars:
                if city[0].lower() == user_var[-1].lower() and city not in self.cities:
                    yield city
            yield None

        self.bot_var = choice(tuple(get_city()))

        if self.bot_var:
            self.cities.append(self.bot_var)
