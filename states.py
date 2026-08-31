from aiogram.fsm.state import State, StatesGroup

class LyricCardStates(StatesGroup):
    waiting_for_audio_or_title = State()
    waiting_for_lyrics = State()
    waiting_for_style = State()
