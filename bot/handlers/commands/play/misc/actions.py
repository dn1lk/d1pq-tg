from enum import Enum


class PlayActions(tuple, Enum):
    __slots__ = ()

    CTS = "cts", "грд"
    RND = "rnd", "рнд"
    RPS = "rps", "кнб"
    UNO = "uno", "уно"
