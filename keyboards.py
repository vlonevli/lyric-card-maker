from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

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
            [KeyboardButton(text="Spotify"), KeyboardButton(text="🎬 YouTube")]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )

def get_customization_keyboard(data: dict) -> InlineKeyboardMarkup:
    """Build an inline keyboard showing current customization selections.
    
    data keys: format, text_color, bg_mode
    """
    fmt = data.get("format", "square")
    tc = data.get("text_color", "white")
    bg = data.get("bg_mode", "albumblur")

    def mark(label, current, value):
        return f"{label} ✓" if current == value else label

    fmt_row = [
        InlineKeyboardButton(text=mark("📐 Square", fmt, "square"), callback_data="fmt:square"),
        InlineKeyboardButton(text=mark("📐 Portrait", fmt, "portrait"), callback_data="fmt:portrait"),
    ]

    tc_row = [
        InlineKeyboardButton(text=mark("⬜ White", tc, "white"), callback_data="tc:white"),
        InlineKeyboardButton(text=mark("⬛ Black", tc, "black"), callback_data="tc:black"),
    ]

    bg_row = [
        InlineKeyboardButton(text=mark("🖼 Album Blur", bg, "albumblur"), callback_data="bg:albumblur"),
        InlineKeyboardButton(text=mark("🎨 Solid", bg, "solid"), callback_data="bg:solid"),
        InlineKeyboardButton(text=mark("🌈 Gradient", bg, "gradient"), callback_data="bg:gradient"),
    ]

    gen_row = [
        InlineKeyboardButton(text="✅ Generate Card", callback_data="generate"),
    ]

    return InlineKeyboardMarkup(inline_keyboard=[fmt_row, tc_row, bg_row, gen_row])
