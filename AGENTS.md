# 🎵 Lyric Card Maker — Agent Reference

> **Purpose**: This file is the single source of truth for any AI agent working on this project.
> Read this fully before making any changes.

---

## 📁 Project Layout

```
F:\pusheds\Lyric card\
│
├── AGENTS.md                  ← YOU ARE HERE
├── bot.py                     ← Telegram bot entry point (webhook + aiohttp server)
├── handlers.py                ← All Telegram message/callback handlers (FSM logic)
├── keyboards.py               ← Reply keyboard builders (menus & style pickers)
├── states.py                  ← aiogram FSM state groups
├── lyric_card.py              ← Spotify-style image generator (PIL/Pillow)
├── requirements.txt           ← Python deps
├── Dockerfile                 ← Python 3.11-slim, exposes port 10000
├── download_assets.py         ← One-time script to fetch fonts + Spotify logo
├── test_lyric_card.py         ← Manual test harness for image generation
│
├── assets/                    ← Static assets used by lyric_card.py
│   ├── Manrope-Bold.ttf
│   ├── Manrope-Regular.ttf
│   ├── Manrope-SemiBold.ttf
│   ├── Vazirmatn-Bold.ttf       ← Arabic/RTL font fallback
│   ├── Vazirmatn-Regular.ttf
│   ├── Vazirmatn-SemiBold.ttf
│   ├── light spotify logo.png
│   └── dark spotify logo.png
│
└── lyrics-card/               ← Standalone web app (YouTube Music style reference)
    ├── index.html             ← Full SPA (HTML + CSS + vanilla JS, ~1864 lines)
    └── api/
        └── lyrics.js          ← Vercel serverless function (Genius API proxy)
```

---

## 🏗️ Architecture Overview

This project has **two separate sub-systems**:

| Sub-system | Tech | Purpose |
|---|---|---|
| **Telegram Bot** | Python, aiogram v3, aiohttp | User-facing bot that generates lyric cards via chat |
| **Web App** (`lyrics-card/`) | Vanilla HTML/CSS/JS | Standalone browser app — YouTube Music style cards |

The bot is deployed on **Render** (`https://lyric-card-maker-1.onrender.com`) using a **webhook** (not polling).

---

## 🤖 Telegram Bot — Deep Dive

### Entry Point: `bot.py`
- Uses **aiogram v3** with an **aiohttp webhook server** on port `10000`
- Environment variables: `BOT_TOKEN`, `WEBHOOK_URL`, `PORT`
- Has a **keep-alive self-ping** every 14 minutes (prevent Render free tier cold starts)
- Sends a deploy notification to admin `chat_id: 430540319` on every startup
- Health check routes: `GET /` and `GET /health` → `"OK - Lyric Card Maker Bot is Healthy"`

### FSM States: `states.py`
```python
class LyricCardStates(StatesGroup):
    waiting_for_audio_or_title = State()   # Step 1: MP3 or "Title - Artist"
    waiting_for_lyrics         = State()   # Step 2: lyrics text
    waiting_for_style          = State()   # Step 3: picks card style button
```

### Conversation Flow (current)
```
/start
  └─► Main Menu (🆕 New Lyric Card)
        └─► [Step 1] Send MP3  OR  type "Song - Artist"
              └─► [Step 2] Send lyrics text
                    └─► [Step 3] Pick style keyboard
                          ├─► "Spotify"   → generates Spotify card → sends image ✅
                          └─► "🎬 YouTube" → PENDING (see TODO)
```

### Keyboards: `keyboards.py`
```python
get_main_menu()   # [🆕 New Lyric Card]
get_style_menu()  # [Spotify]   ← "🎬 YouTube" button needs adding here
```

### Handlers: `handlers.py`
| Handler | Trigger | Action |
|---|---|---|
| `cmd_start` | `/start` | Clears state, shows main menu |
| `process_new_card` | `"🆕 New Lyric Card"` | Sets state → `waiting_for_audio_or_title` |
| `process_audio_or_title` | state + audio or text | Extracts MP3 metadata OR parses "Title - Artist" |
| `process_lyrics` | state + any text | Saves lyrics, shows style menu |
| `process_style` | state + `"Spotify"` | Generates Spotify card, sends photo |

**MP3 metadata tags**: `TIT2` = title, `TPE1` = artist, `APIC` = cover art.  
Temp files saved to `temp/` (auto-created with `os.makedirs`).

---

## 🎨 Spotify Style Engine: `lyric_card.py`

### Class: `SpotifyLyricCardEngine`
```python
engine = SpotifyLyricCardEngine(scale=2)
# scale=2 → all pixel values are doubled for high-DPI output
```

### `generate_card()` Parameters
| Param | Type | Notes |
|---|---|---|
| `lyrics` | str or list | Auto-uppercased; split on `\n`; word-wrapped |
| `song_title` | str | Header area |
| `artist` | str | Header area (80% opacity, uppercased) |
| `album_art_path` | str or None | Used for gradient extraction + thumbnail |
| `color1` | str or None | Hex top gradient; auto-extracted if None |
| `color2` | str or None | Hex bottom gradient; auto-extracted if None |
| `text_color` | str | Hex, default `"#ffffff"` |
| `output_path` | str | Where to save PNG |

### Card Layout (top → bottom)
1. **Header**: album thumbnail (48×48 rounded) + song title + artist
2. **Lyrics block**: large bold Manrope text, word-wrapped, dynamic height
3. **Footer**: Spotify logo PNG + "Spotify" label

### Gradient Extraction Logic
`_extract_dominant_gradient(album_art_path)` → `(color1_hex, color2_hex)`
- Top half → vibrant mid-tone → `color1` (top of gradient)
- Bottom half → dark muted shade → `color2` (bottom)
- Default fallback: `#200407` / `#050102`

### RTL / Arabic Support
- Detects Arabic Unicode ranges
- Switches to `Vazirmatn` font family
- Uses `arabic_reshaper` + `python-bidi` for shaping
- Graceful fallback if libs absent (`HAS_RTL = False`)

### Logo Selection
- `luminance > 128` (bright text) → `light spotify logo.png`
- Dark text → `dark spotify logo.png`

---

## 🌐 Web App — `lyrics-card/`

### `index.html` — 3-page SPA
| Page ID | Description |
|---|---|
| `pageHome` | Search bar + iTunes Top 20 chart grid |
| `pageLyrics` | Song sidebar + clickable lyric lines (select up to 4) |
| `pageCard` | Live card preview + customization panel + PNG download |

### YouTube Music Card Style (web app reference)
The web app uses **YouTube Music** style (NOT Spotify). Key design details:
- **Background**: blurred album art (default) — `filter: blur(32px) brightness(.3) saturate(1.6)`
- **Accent color**: `#ff2020` (YouTube red)
- **Footer logo**: YouTube play-button SVG + "YouTube\nMusic" label
- **Fonts**: `DM Serif Display`, `Sora`, `JetBrains Mono`
- **Card element**: `.lcard` with child `.lcard-ytm` div in the footer
- Card width: 420px square, 340px portrait

### Web App Customization Controls
All available in `pageCard` panel:

| Control | HTML | State key | Options |
|---|---|---|---|
| Card format | `[data-fmt]` buttons | `S.format` | `square` / `portrait` |
| Text color | `[data-tc]` buttons | `S.textColor` | `white` / `black` |
| Background | `[data-bg]` radio divs | `S.bgMode` | `albumblur` / `solid` / `gradient` |
| Solid color | `#solidPick` + `#solidHex` | `S.solid` | Any hex |
| Gradient | `#gc1`, `#gc2`, `#gc3` | `S.grad[]` | 3 color pickers |

### `lyrics-card/api/lyrics.js` — Vercel Proxy
Proxies Genius API. Requires `GENIUS_ACCESS_TOKEN` env var on Vercel.

- `?action=search&query=...` → `[{ id, title, artist, thumbnail, url }]`
- `?action=song&songId=...` → song detail + `lyricsUrl`

Deployed: `https://lyrics-card-taupe.vercel.app/api/lyrics`

### Lyrics Fetch Fallback Chain (web app)
1. Genius (via Vercel proxy)
2. LRCLIB (`https://lrclib.net/api/search`)
3. Lyrics.ovh (`https://api.lyrics.ovh/v1/...`)
4. Manual paste textarea fallback

---

## ✅ Pending TODO List

### 1. Add YouTube Style to Telegram Bot

**`keyboards.py`** — add YouTube button:
```python
def get_style_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Spotify"), KeyboardButton(text="🎬 YouTube")]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )
```

**`lyric_card.py`** — create `YouTubeLyricCardEngine`:
- Inherits or mirrors `SpotifyLyricCardEngine`
- Background: blurred album art (use PIL `ImageFilter.GaussianBlur`)
- Footer: YouTube play-button drawn with PIL (red circle + white triangle)
- Accent: `#FF0000`
- Reference design: `.lcard` + `.lcard-ytm` in `lyrics-card/index.html`

**`handlers.py`** — add YouTube handler:
```python
@router.message(LyricCardStates.waiting_for_style, F.text == "🎬 YouTube")
async def process_style_youtube(message: Message, state: FSMContext):
    # same structure as process_style (Spotify) but calls youtube engine
```

### 2. Post-Style Inline Customization Flow

After user picks a style, offer customizations via **InlineKeyboardMarkup** before generating:

New FSM states needed (add to `states.py`):
```python
waiting_for_background  = State()   # albumblur / solid / gradient
waiting_for_text_color  = State()   # white / black
waiting_for_format      = State()   # square / portrait
```

- Use `CallbackQueryHandler` to handle button presses
- Store choices in FSM: `await state.update_data(bg_mode="albumblur", text_color="white", format="square")`
- Read when generating: `data = await state.get_data()` then pass to `generate_card()`

---

## 🔧 Development Notes

### Running Locally
```bash
pip install -r requirements.txt
python download_assets.py      # one-time: downloads fonts + Spotify logos to assets/
python test_lyric_card.py      # test image generation without the bot
BOT_TOKEN=xxx python bot.py    # starts webhook server
```

### Key Code Patterns
- **CPU-bound image gen** → always offloaded to thread:
  ```python
  output = await asyncio.to_thread(generate_image_sync, song_title=..., ...)
  ```
- **Temp files** → `temp/` dir, auto-created: `os.makedirs("temp", exist_ok=True)`
- **Reading FSM data**: `data = await state.get_data(); val = data.get("key", default)`
- **Updating FSM data**: `await state.update_data(key=value)`
- **Processing messages**: send first (`processing_msg = await message.answer("Processing...")`), delete after done (`await processing_msg.delete()`)

### Deployment (Render)
- Platform: **Render** free tier, Docker container
- Port: `10000` (set via `PORT` env var)
- Webhook auto-set on startup in `on_startup()`
- Self-ping to `/health` every 840 seconds to stay warm

---

## 📦 Python Dependencies

| Package | Purpose |
|---|---|
| `aiogram >= 3.4.0` | Telegram bot framework (async, FSM) |
| `aiohttp >= 3.9.0` | Async HTTP client + webhook web server |
| `Pillow >= 10.0.0` | Image generation (PIL) |
| `mutagen >= 1.47.0` | MP3 metadata reading (ID3 tags) |
| `arabic-reshaper >= 3.0.1` | Arabic text shaping for RTL support |
| `python-bidi >= 0.6.0` | Bidirectional text rendering |
| `python-dotenv >= 1.0.0` | `.env` file loading |

---

## 🗺️ Quick Reference: What to Edit

| I want to... | Edit this file |
|---|---|
| Add a new bot command | `handlers.py` |
| Add a keyboard button | `keyboards.py` |
| Add an FSM state | `states.py` |
| Change Spotify card appearance | `lyric_card.py` → `SpotifyLyricCardEngine` |
| Add YouTube card engine | `lyric_card.py` → new class |
| Change bot startup / webhook | `bot.py` |
| Change web app card design | `lyrics-card/index.html` (`.lcard`, `.lcard-ytm`) |
| Add a web lyrics source | `lyrics-card/index.html` → `openSong()` |
| Change Genius API proxy | `lyrics-card/api/lyrics.js` |
| Add Python dependencies | `requirements.txt` + `Dockerfile` |
