import os
from lyric_card import SpotifyLyricCardEngine
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
    engine = SpotifyLyricCardEngine(scale=2)
    
    with open("lyric.txt", "r", encoding="utf-8") as f:
        sample_lyrics = f.read().strip()
        
    if not sample_lyrics:
        sample_lyrics = "No lyrics found."

    mp3_file = "sample.mp3"
    
    if os.path.exists(mp3_file):
        song, artist, extracted = extract_metadata(mp3_file)
    else:
        song = "Young Metro"
        artist = "Future, Metro Boomin, The Weeknd"
        extracted = None
    
    print(f"Generating lyric card for '{song}' by '{artist}' from {mp3_file}...")
    
    output_file = engine.generate_card(
        lyrics=sample_lyrics,
        song_title=song,
        artist=artist,
        album_art_path=extracted,
        output_path="lyricize_sample_mp3.png",
        color1=None,
        color2=None, 
        text_color="#ffffff"
    )
    print(f"Generated: {output_file}")

if __name__ == "__main__":
    main()
