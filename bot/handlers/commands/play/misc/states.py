from aiogram.fsm.state import StatesGroup, State


class PlayStates(StatesGroup):
    CTS = State()
    RND = State()
    UNO = State()
