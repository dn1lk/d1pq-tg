import secrets
from functools import lru_cache
from pathlib import Path

from pydantic import Field

import config
from handlers.commands.play import PlayData


class CTSData(PlayData):
    bot_city: str | None = None
    used_cities: list[str] = Field(default_factory=list)
    fail_amount: int = 5

    @classmethod
    @lru_cache(maxsize=2)
    def get_cities(cls, locale: str) -> list[str]:
        with Path(f"{config.LOCALE_PATH}/{locale}/cities.txt").open(encoding="utf8") as r:
            return r.read().splitlines()

    def gen_city(self, cities: list[str], user_city: str | None = None) -> None:
        if user_city:
            bot_cities = [
                city for city in cities if city[0].lower() == user_city[-1].lower() and city not in self.used_cities
            ]
        else:
            bot_cities = cities

        self.bot_city = secrets.choice(bot_cities)
        if self.bot_city:
            self.used_cities.append(self.bot_city)
