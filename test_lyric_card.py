import os
from lyric_card import SpotifyLyricCardEngine
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, APIC

def extract_cover(mp3_path, output_jpg):
    try:
        audio = MP3(mp3_path, ID3=ID3)
        for tag in audio.tags.values():
            if isinstance(tag, APIC):
                with open(output_jpg, 'wb') as img:
                    img.write(tag.data)
                return output_jpg
    except Exception as e:
        print(f"Failed to extract cover: {e}")
    return None

def main():
    engine = SpotifyLyricCardEngine(scale=2)
    
    with open("lyric.txt", "r", encoding="utf-8") as f:
        sample_lyrics = f.read().strip()
        
    if not sample_lyrics:
        sample_lyrics = "No lyrics found."

    song = "Young Metro"
    artist = "Future, Metro Boomin, The Weeknd"
    mp3_file = "Future - Young Metro.mp3"
    cover_file = "cover.jpg"
    
    # Extract cover
    extracted = extract_cover(mp3_file, cover_file)
    
    print("Generating sample lyric card for Future - Young Metro...")
    
    # Generate default
    output_file1 = engine.generate_card(
        lyrics=sample_lyrics,
        song_title=song,
        artist=artist,
        album_art_path=extracted,
        output_path="lyricize_sample_future.png",
        color1="#2a0000",
        color2="#000000", 
        text_color="#ffffff"
    )
    print(f"Generated: {output_file1}")

if __name__ == "__main__":
    main()
