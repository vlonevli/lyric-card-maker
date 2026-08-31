import os
import asyncio
from aiogram import Router, F, Bot
from aiogram.types import Message, FSInputFile
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from states import LyricCardStates
from keyboards import get_main_menu, get_style_menu
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, APIC
from lyric_card import SpotifyLyricCardEngine

router = Router()
engine = SpotifyLyricCardEngine(scale=2)

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

def generate_image_sync(song_title, artist, lyrics, cover_path, user_id):
    output_path = f"temp/{user_id}_card.png"
    os.makedirs("temp", exist_ok=True)
    return engine.generate_card(
        lyrics=lyrics,
        song_title=song_title,
        artist=artist,
        album_art_path=cover_path,
        output_path=output_path,
        color1="#121212", # Default dark gradient for now, can be randomized or picked
        color2="#000000",
        text_color="#ffffff"
    )

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

@router.message(LyricCardStates.waiting_for_lyrics, F.text)
async def process_lyrics(message: Message, state: FSMContext):
    await state.update_data(lyrics=message.text)
    await state.set_state(LyricCardStates.waiting_for_style)
    await message.answer(
        "Which lyric card style do you want?",
        reply_markup=get_style_menu()
    )

@router.message(LyricCardStates.waiting_for_style, F.text == "Spotify")
async def process_style(message: Message, state: FSMContext):
    data = await state.get_data()
    
    processing_msg = await message.answer("Processing your lyric card... 🎨", reply_markup=get_main_menu())
    
    try:
        # Offload CPU-bound image generation to a thread!
        output_image_path = await asyncio.to_thread(
            generate_image_sync,
            song_title=data.get("song_title", "Unknown"),
            artist=data.get("artist", "Unknown"),
            lyrics=data.get("lyrics", ""),
            cover_path=data.get("cover_path"),
            user_id=message.from_user.id
        )
        
        # Send the image
        photo = FSInputFile(output_image_path)
        await message.answer_photo(photo=photo, caption="Here is your Lyric Card! 🎧")
        
        # Cleanup temp files if needed (optional)
        # try:
        #     if data.get("mp3_path"): os.remove(data.get("mp3_path"))
        #     if data.get("cover_path"): os.remove(data.get("cover_path"))
        #     if output_image_path: os.remove(output_image_path)
        # except: pass
        
    except Exception as e:
        await message.answer(f"An error occurred while generating the card: {e}")
        
    finally:
        await processing_msg.delete()
        await state.clear()
