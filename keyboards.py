from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def get_main_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🆕 New Lyric Card")]
        ],
        resize_keyboard=True,
        is_persistent=True
    )

def get_style_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Spotify")]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )
