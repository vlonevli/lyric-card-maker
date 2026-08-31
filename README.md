# Lyric Card Maker

A Python library and engine to generate Spotify-styled lyric cards from song lyrics and metadata.

## Features
- **Spotify Style**: Recreates the layout, fonts, rounded corners, and padding from Spotify's lyric cards.
- **Dynamic Gradients**: Custom background gradient generation.
- **Automatic Uppercase Lyrics**: Converts input lyrics to uppercase automatically.
- **MP3 Cover Extraction**: Automatically extracts cover artwork from MP3 files.
- **High Resolution Output**: Clean, anti-aliased output with transparency support.

## Requirements
```bash
pip install -r requirements.txt
```

## Usage
```python
from lyric_card import SpotifyLyricCardEngine

engine = SpotifyLyricCardEngine(scale=2)

output_path = engine.generate_card(
    lyrics="YOUR LYRICS HERE",
    song_title="Song Title",
    artist="Artist Name",
    album_art_path="path/to/cover.jpg",
    output_path="lyric_card.png",
    color1="#1DB954",
    color2="#000000",
    text_color="#ffffff"
)
```
