import os
from PIL import Image, ImageDraw, ImageFont, ImageFilter

try:
    import arabic_reshaper
    from bidi.algorithm import get_display
    HAS_RTL = True
except ImportError:
    HAS_RTL = False

class SpotifyLyricCardEngine:
    def __init__(self, assets_dir=None, scale=2):
        if assets_dir is None:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            possible_dirs = [
                os.path.join(script_dir, "assets"),
                os.path.join(os.path.dirname(script_dir), "assets"),
                r"F:\BOTS AI\Lyric card maker\assets"
            ]
            assets_dir = "assets"
            for d in possible_dirs:
                if os.path.exists(d):
                    assets_dir = d
                    break
        self.assets_dir = assets_dir
        self.scale = scale
        self.base_width = 350
        
        self.font_regular = os.path.join(self.assets_dir, "Manrope-Regular.ttf")
        self.font_semibold = os.path.join(self.assets_dir, "Manrope-SemiBold.ttf")
        self.font_bold = os.path.join(self.assets_dir, "Manrope-Bold.ttf")

    def _reshape(self, text):
        if not text or not isinstance(text, str):
            return text
        if HAS_RTL:
            # Check for Arabic/Persian Unicode characters
            if any('\u0600' <= c <= '\u06FF' or '\u0750' <= c <= '\u077F' or '\u08A0' <= c <= '\u08FF' or '\uFB50' <= c <= '\uFDFF' or '\uFE70' <= c <= '\uFEFF' for c in text):
                reshaped = arabic_reshaper.reshape(text)
                return get_display(reshaped)
        return text

    def _get_font(self, font_path, size):
        try:
            return ImageFont.truetype(font_path, size)
        except IOError:
            # If Manrope fails, use Windows default TrueType fonts so size actually works
            try:
                if "Bold" in font_path:
                    return ImageFont.truetype(r"C:\Windows\Fonts\segoeuib.ttf", size)
                else:
                    return ImageFont.truetype(r"C:\Windows\Fonts\segoeui.ttf", size)
            except:
                return ImageFont.load_default()

    def _draw_rounded_rectangle(self, draw, bounds, radius, fill):
        # A simple rounded rectangle function for PIL
        draw.rounded_rectangle(bounds, radius=radius, fill=fill)

    def _create_gradient(self, width, height, color1, color2):
        base = Image.new('RGB', (width, height), color1)
        top = Image.new('RGB', (width, height), color2)
        mask = Image.new('L', (width, height))
        mask_data = []
        for y in range(height):
            # to bottom gradient
            alpha = int(255 * (y / height))
            mask_data.extend([alpha] * width)
        mask.putdata(mask_data)
        base.paste(top, (0, 0), mask)
        return base

    def generate_card(self, lyrics, song_title, artist, album_art_path=None, 
                      color1="#000000", color2="#290c5e", text_color="#ffffff",
                      output_path="lyric_card.png"):
        s = self.scale
        
        # Dimensions and Layout Specs (scaled)
        padding = 24 * s
        width = self.base_width * s
        
        # Fonts setup
        font_title = self._get_font(self.font_bold, 16 * s)
        font_artist = self._get_font(self.font_bold, 11 * s) # bold instead of regular since uppercase opacity 80
        font_lyrics = self._get_font(self.font_semibold, 20 * s)
        font_footer = self._get_font(self.font_semibold, 14 * s)
        
        # Calculate Height dynamically based on lyrics
        # We need to wrap lyrics (whitespace-pre-wrap in React)
        max_text_width = width - (padding * 2)
        
        # To simulate React's whitespace-pre-wrap, we split by \n
        if isinstance(lyrics, str):
            lyrics = lyrics.upper()
            lines = lyrics.split('\n')
        elif isinstance(lyrics, list):
            lines = [l.upper() for l in lyrics]
        else:
            lines = []
            
        lyric_lines_wrapped = []
        # Create a dummy image to measure text
        dummy_img = Image.new('RGB', (1, 1))
        draw_measure = ImageDraw.Draw(dummy_img)
        
        for line in lines:
            words = line.split()
            if not words:
                lyric_lines_wrapped.append("")
                continue
            
            current_line = words[0]
            for word in words[1:]:
                # Check width of reshaped text
                test_str = self._reshape(current_line + " " + word)
                bbox = draw_measure.textbbox((0, 0), test_str, font=font_lyrics)
                w = bbox[2] - bbox[0]
                if w <= max_text_width:
                    current_line += " " + word
                else:
                    lyric_lines_wrapped.append(current_line)
                    current_line = word
            lyric_lines_wrapped.append(current_line)
            
        # Line height
        line_height = int(20 * s * 1.375) # leading-snug
        lyrics_block_height = len(lyric_lines_wrapped) * line_height
        
        # Calculate total card height
        header_height = 48 * s # 12 units (h-12)
        margin_top_lyrics = 40 * s # mt-10
        margin_top_footer = 24 * s # mt-6
        footer_height = 14 * s
        
        height = padding + header_height + margin_top_lyrics + lyrics_block_height + margin_top_footer + footer_height + padding
        
        # 1. Create Base with Gradient
        # Convert hex to RGB
        c1 = tuple(int(color1.lstrip('#')[i:i+2], 16) for i in (0, 2, 4))
        c2 = tuple(int(color2.lstrip('#')[i:i+2], 16) for i in (0, 2, 4))
        
        img = self._create_gradient(width, height, c1, c2)
        draw = ImageDraw.Draw(img)
        
        current_y = padding
        
        # 2. Draw Header (Album Art + Info)
        album_size = 48 * s
        album_radius = 8 * s
        
        if album_art_path and os.path.exists(album_art_path):
            try:
                album_img = Image.open(album_art_path).convert("RGBA")
                album_img = album_img.resize((album_size, album_size), Image.LANCZOS)
                
                # Apply rounded mask
                mask = Image.new("L", (album_size, album_size), 0)
                mask_draw = ImageDraw.Draw(mask)
                mask_draw.rounded_rectangle([(0,0), (album_size, album_size)], radius=album_radius, fill=255)
                
                album_img.putalpha(mask)
                img.paste(album_img, (padding, current_y), album_img)
            except Exception as e:
                print(f"Error loading album art: {e}")
                draw.rounded_rectangle([(padding, current_y), (padding + album_size, current_y + album_size)], radius=album_radius, fill=(100, 100, 100))
        else:
            # Placeholder gray box for album art
            draw.rounded_rectangle([(padding, current_y), (padding + album_size, current_y + album_size)], radius=album_radius, fill=(100, 100, 100))
            
        # Draw Song Info
        text_x = padding + album_size + (16 * s) # space-x-4
        
        reshaped_title = self._reshape(song_title)
        reshaped_artist = self._reshape(artist.upper())
        
        # Center text vertically relative to album art
        # Title
        title_bbox = draw.textbbox((0, 0), reshaped_title, font=font_title)
        title_h = title_bbox[3] - title_bbox[1]
        
        # Artist
        artist_bbox = draw.textbbox((0, 0), reshaped_artist, font=font_artist)
        artist_h = artist_bbox[3] - artist_bbox[1]
        
        title_artist_gap = int(25 * (s / 2)) # ~25px gap between title and artist
        total_info_h = title_h + artist_h + title_artist_gap
        info_start_y = current_y + (album_size - total_info_h) // 2
        
        draw.text((text_x, info_start_y), reshaped_title, font=font_title, fill=text_color)
        
        # Artist text has 80% opacity
        # Convert hex to RGBA text_color with 80% alpha (204)
        tc = tuple(int(text_color.lstrip('#')[i:i+2], 16) for i in (0, 2, 4))
        artist_tc = (*tc, int(255 * 0.8))
        
        # Create a transparent overlay for artist text to support alpha
        overlay = Image.new("RGBA", img.size, (255,255,255,0))
        overlay_draw = ImageDraw.Draw(overlay)
        overlay_draw.text((text_x, info_start_y + title_h + title_artist_gap), reshaped_artist, font=font_artist, fill=artist_tc)
        img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")
        draw = ImageDraw.Draw(img) # Refresh draw object
        
        # 3. Draw Lyrics
        current_y += album_size + margin_top_lyrics
        
        for line in lyric_lines_wrapped:
            reshaped_line = self._reshape(line)
            draw.text((padding, current_y), reshaped_line, font=font_lyrics, fill=text_color)
            current_y += line_height
            
        # 4. Draw Footer
        current_y = height - padding - footer_height
        
        logo_size = int(14 * s * 1.5) # slightly larger than text for visual balance
        logo_y = current_y + (footer_height - logo_size) // 2
        
        # Determine whether to use light or dark logo based on text_color
        tc_r, tc_g, tc_b = (int(text_color.lstrip('#')[i:i+2], 16) for i in (0, 2, 4))
        luminance = (0.299*tc_r + 0.587*tc_g + 0.114*tc_b)
        
        if luminance > 128:
            logo_file = "light spotify logo.png"
        else:
            logo_file = "dark spotify logo.png"
            
        logo_path = os.path.join(self.assets_dir, logo_file)
        
        if os.path.exists(logo_path):
            try:
                logo_img = Image.open(logo_path).convert("RGBA")
                # Maintain aspect ratio for the logo
                aspect = logo_img.width / logo_img.height
                new_w = int(logo_size * aspect)
                logo_img = logo_img.resize((new_w, logo_size), Image.LANCZOS)
                img.paste(logo_img, (padding, logo_y), logo_img)
                logo_width = new_w
            except Exception as e:
                print(f"Error loading logo: {e}")
                draw.ellipse([(padding, logo_y), (padding + logo_size, logo_y + logo_size)], fill="#1DB954")
                logo_width = logo_size
        else:
            draw.ellipse([(padding, logo_y), (padding + logo_size, logo_y + logo_size)], fill="#1DB954")
            logo_width = logo_size
            
        # Spotify Text
        spotify_text_x = padding + logo_width + (4 * s) # space-x-1
        draw.text((spotify_text_x, current_y), "Spotify", font=font_footer, fill=text_color)
        
        # Finally, we want the whole card to have rounded corners (like `rounded-lg`)
        # Create a mask for the final image
        final_radius = 8 * s
        mask = Image.new("L", img.size, 0)
        mask_draw = ImageDraw.Draw(mask)
        mask_draw.rounded_rectangle([(0,0), img.size], radius=final_radius, fill=255)
        
        # Create a transparent image to paste the masked card onto
        final_img = Image.new("RGBA", img.size, (0,0,0,0))
        img.putalpha(mask)
        final_img.paste(img, (0,0))
        
        # Save as PNG to keep transparency
        final_img.save(output_path, format="PNG")
        return output_path

if __name__ == "__main__":
    pass
