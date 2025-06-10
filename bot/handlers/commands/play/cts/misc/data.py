import secrets
from functools import lru_cache

from pydantic import Field

import misc
from handlers.commands.play import PlayData


class CTSData(PlayData):
    bot_city: str | None = None
    used_cities: list[str] = Field(default_factory=list)
    fail_amount: int = 5

    @classmethod
    @lru_cache(maxsize=2)
    def get_cities(cls, locale: str) -> list[str]:
        path = misc.LOCALE_PATH / locale / "cities.txt"
        return path.read_text(encoding="UTF-8").splitlines()

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
