import os
import asyncio
from aiogram import Router, F, Bot
from aiogram.types import Message, FSInputFile, CallbackQuery
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from states import LyricCardStates
from keyboards import get_main_menu, get_style_menu, get_customization_keyboard
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, APIC
from lyric_card import SpotifyLyricCardEngine, YouTubeLyricCardEngine

router = Router()
spotify_engine = SpotifyLyricCardEngine(scale=2)
youtube_engine = YouTubeLyricCardEngine(scale=2)

def extract_metadata(mp3_path, output_cover_dir="temp"):
    title = "Unknown Song"
    artist = "Unknown Artist"
    cover_path = os.path.join(output_cover_dir, f"{os.path.basename(mp3_path)}_cover.jpg")
    extracted_cover = None
    
    try:
        audio = MP3(mp3_path, ID3=ID3)
        if audio.tags:
            if 'TIT2' in audio.tags:
                title = str(audio.tags['TIT2'])
            if 'TPE1' in audio.tags:
                artist = str(audio.tags['TPE1'])
            for tag in audio.tags.values():
                if isinstance(tag, APIC):
                    os.makedirs(output_cover_dir, exist_ok=True)
                    with open(cover_path, 'wb') as img:
                        img.write(tag.data)
                    extracted_cover = cover_path
                    break
    except Exception as e:
        print(f"Error reading metadata: {e}")
        
    return title, artist, extracted_cover

def generate_spotify_image_sync(song_title, artist, lyrics, cover_path, user_id,
                                text_color="#ffffff", bg_mode="albumblur", 
                                card_format="square", solid_color="#1a1a1a",
                                grad_colors=None):
    """Generate a Spotify-style card with customization options."""
    output_path = f"temp/{user_id}_card.png"
    os.makedirs("temp", exist_ok=True)
    
    # For Spotify, bg_mode defaults to gradient from album art (original behavior)
    # but we still support solid/gradient if user picks them
    if bg_mode == "albumblur":
        # Spotify doesn't have album blur — use its original gradient behavior
        return spotify_engine.generate_card(
            lyrics=lyrics,
            song_title=song_title,
            artist=artist,
            album_art_path=cover_path,
            output_path=output_path,
            color1=None,
            color2=None,
            text_color=text_color
        )
    else:
        # For solid/gradient, use default dark colors
        return spotify_engine.generate_card(
            lyrics=lyrics,
            song_title=song_title,
            artist=artist,
            album_art_path=cover_path,
            output_path=output_path,
            color1=solid_color if bg_mode == "solid" else (grad_colors[0] if grad_colors else "#0f0c29"),
            color2=solid_color if bg_mode == "solid" else (grad_colors[2] if grad_colors else "#24243e"),
            text_color=text_color
        )

def generate_youtube_image_sync(song_title, artist, lyrics, cover_path, user_id,
                                text_color="#ffffff", bg_mode="albumblur",
                                card_format="square", solid_color="#1a1a1a",
                                grad_colors=None):
    """Generate a YouTube Music style card with customization options."""
    output_path = f"temp/{user_id}_yt_card.png"
    os.makedirs("temp", exist_ok=True)
    return youtube_engine.generate_card(
        lyrics=lyrics,
        song_title=song_title,
        artist=artist,
        album_art_path=cover_path,
        output_path=output_path,
        text_color=text_color,
        bg_mode=bg_mode,
        format=card_format,
        solid_color=solid_color,
        grad_colors=grad_colors
    )

# ── Commands ──────────────────────────────────────────────────────

@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "Welcome to the Lyric Card Maker Bot! 🎵\nClick the button below to start.",
        reply_markup=get_main_menu()
    )

@router.message(F.text == "🆕 New Lyric Card")
async def process_new_card(message: Message, state: FSMContext):
    await state.set_state(LyricCardStates.waiting_for_audio_or_title)
    await message.answer(
        "Please send the song file (.mp3) to extract the cover and tags,\n"
        "OR type the Song Title and Artist (e.g., 'Young Metro - Future')."
    )

# ── Step 1: Audio or Title ────────────────────────────────────────

@router.message(LyricCardStates.waiting_for_audio_or_title)
async def process_audio_or_title(message: Message, state: FSMContext, bot: Bot):
    os.makedirs("temp", exist_ok=True)
    
    if message.audio:
        # It's an audio file
        processing_msg = await message.answer("Downloading audio file...")
        file_id = message.audio.file_id
        file = await bot.get_file(file_id)
        file_path = file.file_path
        
        local_mp3_path = f"temp/{file_id}.mp3"
        await bot.download_file(file_path, destination=local_mp3_path)
        
        await processing_msg.edit_text("Extracting metadata...")
        
        # Offload metadata extraction to thread to avoid blocking if file is large
        title, artist, cover_path = await asyncio.to_thread(extract_metadata, local_mp3_path, "temp")
        
        await state.update_data(
            song_title=title,
            artist=artist,
            cover_path=cover_path,
            mp3_path=local_mp3_path
        )
        
        await processing_msg.delete()
        await message.answer(
            f"Extracted Metadata:\n🎵 **Title**: {title}\n🎤 **Artist**: {artist}\n\n"
            "Great! Now, please send the lyrics text you want on the card.",
            parse_mode="Markdown"
        )
        
    elif message.text:
        # User sent text (Title - Artist)
        text = message.text
        parts = text.split("-")
        title = parts[0].strip()
        artist = parts[1].strip() if len(parts) > 1 else "Unknown Artist"
        
        await state.update_data(
            song_title=title,
            artist=artist,
            cover_path=None
        )
        await message.answer("Great! Now, please send the lyrics text you want on the card.")
        
    else:
        await message.answer("Please send an audio file or text.")
        return

    await state.set_state(LyricCardStates.waiting_for_lyrics)

# ── Step 2: Lyrics ────────────────────────────────────────────────

@router.message(LyricCardStates.waiting_for_lyrics, F.text)
async def process_lyrics(message: Message, state: FSMContext):
    await state.update_data(lyrics=message.text)
    await state.set_state(LyricCardStates.waiting_for_style)
    await message.answer(
        "Which lyric card style do you want?",
        reply_markup=get_style_menu()
    )

# ── Step 3: Style Selection ──────────────────────────────────────

@router.message(LyricCardStates.waiting_for_style, F.text == "Spotify")
async def process_style_spotify(message: Message, state: FSMContext):
    # Save style + set defaults for customization
    await state.update_data(
        style="spotify",
        format="square",
        text_color="white",
        bg_mode="albumblur"
    )
    await state.set_state(LyricCardStates.waiting_for_customization)
    
    data = await state.get_data()
    await message.answer(
        "🎨 *Customize your Spotify card:*\n"
        "Tap the options below, then hit *✅ Generate Card* when ready.",
        parse_mode="Markdown",
        reply_markup=get_customization_keyboard(data)
    )

@router.message(LyricCardStates.waiting_for_style, F.text == "🎬 YouTube")
async def process_style_youtube(message: Message, state: FSMContext):
    # Save style + set defaults for customization
    await state.update_data(
        style="youtube",
        format="square",
        text_color="white",
        bg_mode="albumblur"
    )
    await state.set_state(LyricCardStates.waiting_for_customization)
    
    data = await state.get_data()
    await message.answer(
        "🎨 *Customize your YouTube Music card:*\n"
        "Tap the options below, then hit *✅ Generate Card* when ready.",
        parse_mode="Markdown",
        reply_markup=get_customization_keyboard(data)
    )

# ── Step 4: Customization Inline Keyboard Callbacks ──────────────

@router.callback_query(LyricCardStates.waiting_for_customization, F.data.startswith("fmt:"))
async def cb_format(callback: CallbackQuery, state: FSMContext):
    value = callback.data.split(":")[1]
    await state.update_data(format=value)
    data = await state.get_data()
    await callback.message.edit_reply_markup(reply_markup=get_customization_keyboard(data))
    await callback.answer(f"Format: {value}")

@router.callback_query(LyricCardStates.waiting_for_customization, F.data.startswith("tc:"))
async def cb_text_color(callback: CallbackQuery, state: FSMContext):
    value = callback.data.split(":")[1]
    await state.update_data(text_color=value)
    data = await state.get_data()
    await callback.message.edit_reply_markup(reply_markup=get_customization_keyboard(data))
    await callback.answer(f"Text color: {value}")

@router.callback_query(LyricCardStates.waiting_for_customization, F.data.startswith("bg:"))
async def cb_bg_mode(callback: CallbackQuery, state: FSMContext):
    value = callback.data.split(":")[1]
    await state.update_data(bg_mode=value)
    data = await state.get_data()
    await callback.message.edit_reply_markup(reply_markup=get_customization_keyboard(data))
    await callback.answer(f"Background: {value}")

@router.callback_query(LyricCardStates.waiting_for_customization, F.data == "generate")
async def cb_generate(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    
    # Remove inline keyboard and show processing message
    await callback.message.edit_text("Processing your lyric card... 🎨")
    
    style = data.get("style", "spotify")
    text_color = "#ffffff" if data.get("text_color", "white") == "white" else "#111111"
    bg_mode = data.get("bg_mode", "albumblur")
    card_format = data.get("format", "square")
    
    try:
        if style == "youtube":
            output_image_path = await asyncio.to_thread(
                generate_youtube_image_sync,
                song_title=data.get("song_title", "Unknown"),
                artist=data.get("artist", "Unknown"),
                lyrics=data.get("lyrics", ""),
                cover_path=data.get("cover_path"),
                user_id=callback.from_user.id,
                text_color=text_color,
                bg_mode=bg_mode,
                card_format=card_format,
            )
        else:
            output_image_path = await asyncio.to_thread(
                generate_spotify_image_sync,
                song_title=data.get("song_title", "Unknown"),
                artist=data.get("artist", "Unknown"),
                lyrics=data.get("lyrics", ""),
                cover_path=data.get("cover_path"),
                user_id=callback.from_user.id,
                text_color=text_color,
                bg_mode=bg_mode,
                card_format=card_format,
            )
        
        # Send the image
        photo = FSInputFile(output_image_path)
        style_label = "YouTube Music" if style == "youtube" else "Spotify"
        await callback.message.answer_photo(
            photo=photo, 
            caption=f"Here is your {style_label} Lyric Card! 🎧",
            reply_markup=get_main_menu()
        )
        
    except Exception as e:
        await callback.message.answer(
            f"An error occurred while generating the card: {e}",
            reply_markup=get_main_menu()
        )
        
    finally:
        # Delete the "Processing..." message
        try:
            await callback.message.delete()
        except:
            pass
        await state.clear()
    
    await callback.answer()
