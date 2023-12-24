from aiogram.fsm.state import StatesGroup, State


class GPTSettingsStates(StatesGroup):
    MAX_TOKENS = State()
