from aiogram.fsm.state import State, StatesGroup


class PlayStates(StatesGroup):
    CTS = State()
    RND = State()
    UNO = State()
