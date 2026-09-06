import os
from lyric_card import SpotifyLyricCardEngine, YouTubeLyricCardEngine
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, APIC

def extract_metadata(mp3_path):
    title = "Unknown Song"
    artist = "Unknown Artist"
    cover_path = "cover.jpg"
    extracted_cover = None
    
    try:
        audio = MP3(mp3_path, ID3=ID3)
        if audio.tags:
            # Title
            if 'TIT2' in audio.tags:
                title = str(audio.tags['TIT2'])
            # Artist
            if 'TPE1' in audio.tags:
                artist = str(audio.tags['TPE1'])
            # Cover
            for tag in audio.tags.values():
                if isinstance(tag, APIC):
                    with open(cover_path, 'wb') as img:
                        img.write(tag.data)
                    extracted_cover = cover_path
                    break
    except Exception as e:
        print(f"Error reading metadata: {e}")
        
    return title, artist, extracted_cover

def main():
    spotify_engine = SpotifyLyricCardEngine(scale=2)
    youtube_engine = YouTubeLyricCardEngine(scale=2)
    
    with open("lyric.txt", "r", encoding="utf-8") as f:
        sample_lyrics = f.read().strip()
        
    if not sample_lyrics:
        sample_lyrics = "Feed me dope"

    # Test 1: sample.mp3 (Drake - Hate Sleeping Alone or extracted)
    mp3_file = "sample.mp3"
    if os.path.exists(mp3_file):
        song, artist, extracted = extract_metadata(mp3_file)
        print(f"\n--- Generating SPOTIFY lyric card for '{song}' by '{artist}' ---")
        if extracted and os.path.exists(extracted):
            c1, c2 = spotify_engine._extract_dominant_gradient(extracted)
            print(f"Extracted gradient from '{extracted}': Top={c1}, Bottom={c2}")
        
        output1 = spotify_engine.generate_card(
            lyrics=sample_lyrics,
            song_title=song,
            artist=artist,
            album_art_path=extracted,
            output_path="lyricize_sample_mp3.png"
        )
        print(f"Generated: {output1}")

    # Test 2: Future, Metro Boomin - Young Metro
    future_cover = "future_cover.png" if os.path.exists("future_cover.png") else "cover.jpg"
    future_song = "Young Metro"
    future_artist = "Future, Metro Boomin, The Weeknd"
    future_lyrics = "Young Metro, Young Metro, Young Metro\nFeed me dope"
    
    print(f"\n--- Generating SPOTIFY lyric card for '{future_song}' by '{future_artist}' ---")
    if os.path.exists(future_cover):
        c1, c2 = spotify_engine._extract_dominant_gradient(future_cover)
        print(f"Extracted gradient from '{future_cover}': Top={c1}, Bottom={c2}")
        
    output2 = spotify_engine.generate_card(
        lyrics=future_lyrics,
        song_title=future_song,
        artist=future_artist,
        album_art_path=future_cover,
        output_path="lyricize_sample_future.png"
    )
    print(f"Generated: {output2}")

    # ── YouTube Music Style Tests ──────────────────────────────────

    print("\n" + "=" * 60)
    print("YOUTUBE MUSIC STYLE TESTS")
    print("=" * 60)

    # Test 3: YouTube - Album Blur (default)
    print(f"\n--- Generating YOUTUBE card (albumblur) for '{future_song}' ---")
    output3 = youtube_engine.generate_card(
        lyrics=future_lyrics,
        song_title=future_song,
        artist=future_artist,
        album_art_path=future_cover,
        output_path="lyricize_yt_albumblur.png",
        bg_mode="albumblur",
        format="square"
    )
    print(f"Generated: {output3}")

    # Test 4: YouTube - Solid background
    print(f"\n--- Generating YOUTUBE card (solid) for '{future_song}' ---")
    output4 = youtube_engine.generate_card(
        lyrics=future_lyrics,
        song_title=future_song,
        artist=future_artist,
        album_art_path=future_cover,
        output_path="lyricize_yt_solid.png",
        bg_mode="solid",
        solid_color="#1a1a2e",
        format="square"
    )
    print(f"Generated: {output4}")

    # Test 5: YouTube - Gradient background
    print(f"\n--- Generating YOUTUBE card (gradient) for '{future_song}' ---")
    output5 = youtube_engine.generate_card(
        lyrics=future_lyrics,
        song_title=future_song,
        artist=future_artist,
        album_art_path=future_cover,
        output_path="lyricize_yt_gradient.png",
        bg_mode="gradient",
        grad_colors=["#0f0c29", "#302b63", "#24243e"],
        format="square"
    )
    print(f"Generated: {output5}")

    # Test 6: YouTube - Portrait format
    print(f"\n--- Generating YOUTUBE card (portrait) for '{future_song}' ---")
    output6 = youtube_engine.generate_card(
        lyrics=future_lyrics,
        song_title=future_song,
        artist=future_artist,
        album_art_path=future_cover,
        output_path="lyricize_yt_portrait.png",
        bg_mode="albumblur",
        format="portrait"
    )
    print(f"Generated: {output6}")

    # Test 7: YouTube - Black text
    print(f"\n--- Generating YOUTUBE card (black text) for '{future_song}' ---")
    output7 = youtube_engine.generate_card(
        lyrics=future_lyrics,
        song_title=future_song,
        artist=future_artist,
        album_art_path=future_cover,
        output_path="lyricize_yt_blacktext.png",
        bg_mode="solid",
        solid_color="#e0e0e0",
        text_color="#111111",
        format="square"
    )
    print(f"Generated: {output7}")

if __name__ == "__main__":
    main()
