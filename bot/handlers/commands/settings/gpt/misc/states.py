from aiogram.fsm.state import State, StatesGroup


class GPTSettingsStates(StatesGroup):
    MAX_TOKENS = State()
