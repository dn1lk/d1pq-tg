from random import choice

from pydantic import BaseModel

from bot import filters as f
from . import get_cts


class CtsData(BaseModel):
    bot_var: str | None
    cities: list[str]
    fails: int = 5

    async def var_filter(self, locale: str, user_var: str):
        def user_var_filter():
            for game_var in game_vars:
                if game_var[0].lower() == user_var[0].lower():
                    yield f.LevenshteinFilter.lev_distance(game_var, user_var) <= len(game_var) / 3

        if not self.bot_var or user_var[0].lower() == self.bot_var[-1].lower():
            if user_var not in self.cities:
                game_vars = get_cts(locale)

                if any(user_var_filter()):
                    self.cities.append(user_var)
                    self.gen_bot_var(user_var, game_vars)

                    return self.bot_var

    def gen_bot_var(self, user_var: str, game_vars: list[str]):
        def get_var():
            for city in game_vars:
                if city[0].lower() == user_var[-1].lower() and city not in self.cities:
                    yield city
            yield None

        self.bot_var = choice(tuple(get_var()))

        if self.bot_var:
            self.cities.append(self.bot_var)
