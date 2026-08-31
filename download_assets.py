import urllib.request
import os

os.makedirs("assets", exist_ok=True)

# Manrope fonts
fonts = {
    "Manrope-Bold.ttf": "https://github.com/google/fonts/raw/main/ofl/manrope/Manrope%5Bwght%5D.ttf", # Variable font, we can just use the regular/bold by setting size or download static ones
    # Let's download static ones for better PIL compatibility
    "Manrope-Regular.ttf": "https://github.com/google/fonts/raw/main/ofl/manrope/static/Manrope-Regular.ttf",
    "Manrope-SemiBold.ttf": "https://github.com/google/fonts/raw/main/ofl/manrope/static/Manrope-SemiBold.ttf",
    "Manrope-Bold.ttf": "https://github.com/google/fonts/raw/main/ofl/manrope/static/Manrope-Bold.ttf",
}

# Spotify logo (white png)
spotify_logo_url = "https://storage.googleapis.com/pr-newsroom-wp/1/2018/11/Spotify_Icon_RGB_White.png"

for name, url in fonts.items():
    path = os.path.join("assets", name)
    print(f"Downloading {name}...")
    try:
        urllib.request.urlretrieve(url, path)
        print(f"Saved to {path}")
    except Exception as e:
        print(f"Failed to download {name}: {e}")

logo_path = os.path.join("assets", "spotify_logo.png")
try:
    print("Downloading Spotify logo...")
    urllib.request.urlretrieve(spotify_logo_url, logo_path)
    print(f"Saved to {logo_path}")
except Exception as e:
    print(f"Failed to download logo: {e}")
