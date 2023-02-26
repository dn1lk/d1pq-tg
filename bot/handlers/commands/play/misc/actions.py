from enum import Enum


class PlayActions(tuple, Enum):
    CTS = 'cts', 'грд'
    RND = 'rnd', 'рнд'
    RPS = 'rps', 'кнб'
    UNO = 'uno', 'уно'
