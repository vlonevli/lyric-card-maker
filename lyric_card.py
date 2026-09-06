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

    def _has_rtl(self, text):
        if not text or not isinstance(text, str):
            return False
        return any('\u0600' <= c <= '\u06FF' or '\u0750' <= c <= '\u077F' or '\u08A0' <= c <= '\u08FF' or '\uFB50' <= c <= '\uFDFF' or '\uFE70' <= c <= '\uFEFF' for c in text)

    def _reshape(self, text):
        if not text or not isinstance(text, str):
            return text
        if HAS_RTL and self._has_rtl(text):
            reshaped = arabic_reshaper.reshape(text)
            return get_display(reshaped)
        return text

    def _get_font(self, font_path, size, text=""):
        if self._has_rtl(text):
            if "Bold" in font_path:
                vazir_name = "Vazirmatn-Bold.ttf"
            elif "SemiBold" in font_path:
                vazir_name = "Vazirmatn-SemiBold.ttf"
            else:
                vazir_name = "Vazirmatn-Regular.ttf"
            
            vazir_path = os.path.join(self.assets_dir, vazir_name)
            if os.path.exists(vazir_path):
                font_path = vazir_path

        try:
            return ImageFont.truetype(font_path, size)
        except IOError:
            try:
                if "Bold" in font_path:
                    return ImageFont.truetype(r"C:\Windows\Fonts\segoeuib.ttf", size)
                else:
                    return ImageFont.truetype(r"C:\Windows\Fonts\segoeui.ttf", size)
            except:
                return ImageFont.load_default()

    def _get_vibrant_color(self, img_crop):
        try:
            small = img_crop.resize((100, 100))
            quantized = small.quantize(colors=16)
            palette = quantized.getpalette()[:48]
            color_counts = quantized.getcolors()
            
            if not color_counts:
                return None
                
            best_color = None
            best_score = -1
            
            for count, index in color_counts:
                r = palette[index * 3]
                g = palette[index * 3 + 1]
                b = palette[index * 3 + 2]
                
                max_c = max(r, g, b)
                min_c = min(r, g, b)
                lightness = (max_c + min_c) / 510.0
                delta = (max_c - min_c) / 255.0
                
                saturation = 0 if max_c == min_c else delta / (1 - abs(2 * lightness - 1))
                
                # Filter out pure whites / blacks
                if lightness < 0.05 or lightness > 0.95:
                    continue
                    
                lightness_score = 1.0 - abs(lightness - 0.45) * 1.2
                score = (count ** 0.5) * ((saturation + 0.1) ** 1.5) * max(0.1, lightness_score)
                
                if score > best_score:
                    best_score = score
                    best_color = (r, g, b)
                    
            if best_color is None and color_counts:
                color_counts.sort(key=lambda x: x[0], reverse=True)
                idx = color_counts[0][1]
                best_color = (palette[idx*3], palette[idx*3+1], palette[idx*3+2])
                
            return best_color
        except Exception:
            return None

    def _extract_dominant_gradient(self, album_art_path):
        default_c1 = "#200407"
        default_c2 = "#050102"
        if not album_art_path or not os.path.exists(album_art_path):
            return default_c1, default_c2
        try:
            img = Image.open(album_art_path).convert("RGB")
            w, h = img.size
            top_crop = img.crop((0, 0, w, int(h * 0.5)))
            bottom_crop = img.crop((0, int(h * 0.5), w, h))
            
            c1_rgb = self._get_vibrant_color(top_crop) or self._get_vibrant_color(img)
            c2_rgb = self._get_vibrant_color(bottom_crop) or self._get_vibrant_color(img)
            
            if not c1_rgb:
                return default_c1, default_c2
                
            # Tone c1 to ensure it is vibrant but well-balanced for Spotify lyric cards
            r1, g1, b1 = c1_rgb
            max1 = max(r1, g1, b1)
            if max1 > 0:
                if max1 > 200:
                    factor = 180 / max1
                    r1, g1, b1 = int(r1 * factor), int(g1 * factor), int(b1 * factor)
                elif max1 < 80:
                    factor = 120 / max1
                    r1, g1, b1 = min(255, int(r1 * factor)), min(255, int(g1 * factor)), min(255, int(b1 * factor))
            c1_rgb = (r1, g1, b1)

            # Generate bottom color c2: deep dark shade of c1 or c2_rgb
            if c2_rgb:
                r2, g2, b2 = c2_rgb
                max2 = max(r2, g2, b2)
                if max2 > 0:
                    target_max = min(80, int(max2 * 0.5))
                    factor = target_max / max2
                    r2, g2, b2 = int(r2 * factor), int(g2 * factor), int(b2 * factor)
                c2_rgb = (r2, g2, b2)
            else:
                c2_rgb = (int(r1 * 0.2), int(g1 * 0.2), int(b1 * 0.2))

            c1_hex = f"#{c1_rgb[0]:02x}{c1_rgb[1]:02x}{c1_rgb[2]:02x}"
            c2_hex = f"#{c2_rgb[0]:02x}{c2_rgb[1]:02x}{c2_rgb[2]:02x}"
            return c1_hex, c2_hex
        except Exception as e:
            print(f"Error extracting gradient color: {e}")
            return default_c1, default_c2

    def _draw_rounded_rectangle(self, draw, bounds, radius, fill):
        # A simple rounded rectangle function for PIL
        draw.rounded_rectangle(bounds, radius=radius, fill=fill)

    def _create_gradient(self, width, height, color1, color2):
        base = Image.new('RGB', (width, height), color1)
        top = Image.new('RGB', (width, height), color2)
        mask = Image.new('L', (width, height))
        mask_data = []
        for y in range(height):
            ratio = y / max(1, height - 1)
            # Smooth curve easing for Spotify vertical gradient transition
            curve = ratio ** 1.3
            alpha = int(255 * curve)
            mask_data.extend([alpha] * width)
        mask.putdata(mask_data)
        base.paste(top, (0, 0), mask)
        return base

    def generate_card(self, lyrics, song_title, artist, album_art_path=None, 
                      color1=None, color2=None, text_color="#ffffff",
                      output_path="lyric_card.png"):
        s = self.scale
        
        if color1 is None or color2 is None:
            extracted_c1, extracted_c2 = self._extract_dominant_gradient(album_art_path)
            color1 = color1 or extracted_c1
            color2 = color2 or extracted_c2
        
        # Dimensions and Layout Specs (scaled)
        padding = 24 * s
        width = self.base_width * s
        
        # Fonts setup (heavy bold typography matching premium Spotify design)
        font_title = self._get_font(self.font_bold, 18 * s, text=song_title)
        font_artist = self._get_font(self.font_bold, 12 * s, text=artist)
        font_lyrics = self._get_font(self.font_bold, 24 * s, text=str(lyrics))
        font_footer = self._get_font(self.font_bold, 14 * s)
        
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
        line_height = int(24 * s * 1.35)
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
        
        # Rounded container corners matching premium Spotify card design
        final_radius = 12 * s
        mask = Image.new("L", img.size, 0)
        mask_draw = ImageDraw.Draw(mask)
        mask_draw.rounded_rectangle([(0,0), img.size], radius=final_radius, fill=255)
        
        final_img = Image.new("RGBA", img.size, (0,0,0,0))
        img.putalpha(mask)
        final_img.paste(img, (0,0))
        
        final_img.save(output_path, format="PNG")
        return output_path

class YouTubeLyricCardEngine:
    """YouTube Music style lyric card generator.
    
    Based on the web app design in lyrics-card/index.html.
    Supports 3 background modes: albumblur, solid, gradient.
    Supports square and portrait formats.
    """
    
    def __init__(self, assets_dir=None, scale=2):
        if assets_dir is None:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            possible_dirs = [
                os.path.join(script_dir, "assets"),
                os.path.join(os.path.dirname(script_dir), "assets"),
            ]
            assets_dir = "assets"
            for d in possible_dirs:
                if os.path.exists(d):
                    assets_dir = d
                    break
        self.assets_dir = assets_dir
        self.scale = scale
        
        self.font_regular = os.path.join(self.assets_dir, "Manrope-Regular.ttf")
        self.font_semibold = os.path.join(self.assets_dir, "Manrope-SemiBold.ttf")
        self.font_bold = os.path.join(self.assets_dir, "Manrope-Bold.ttf")

    # ── Shared helpers (same as Spotify engine) ──────────────────────

    def _has_rtl(self, text):
        if not text or not isinstance(text, str):
            return False
        return any('\u0600' <= c <= '\u06FF' or '\u0750' <= c <= '\u077F' or '\u08A0' <= c <= '\u08FF' or '\uFB50' <= c <= '\uFDFF' or '\uFE70' <= c <= '\uFEFF' for c in text)

    def _reshape(self, text):
        if not text or not isinstance(text, str):
            return text
        if HAS_RTL and self._has_rtl(text):
            reshaped = arabic_reshaper.reshape(text)
            return get_display(reshaped)
        return text

    def _get_font(self, font_path, size, text=""):
        if self._has_rtl(text):
            if "Bold" in font_path:
                vazir_name = "Vazirmatn-Bold.ttf"
            elif "SemiBold" in font_path:
                vazir_name = "Vazirmatn-SemiBold.ttf"
            else:
                vazir_name = "Vazirmatn-Regular.ttf"
            vazir_path = os.path.join(self.assets_dir, vazir_name)
            if os.path.exists(vazir_path):
                font_path = vazir_path
        try:
            return ImageFont.truetype(font_path, size)
        except IOError:
            try:
                if "Bold" in font_path:
                    return ImageFont.truetype(r"C:\Windows\Fonts\segoeuib.ttf", size)
                else:
                    return ImageFont.truetype(r"C:\Windows\Fonts\segoeui.ttf", size)
            except:
                return ImageFont.load_default()

    # ── Background renderers ─────────────────────────────────────────

    def _create_albumblur_bg(self, width, height, album_art_path):
        """Blurred album art background matching web app: blur(32px) brightness(.3) saturate(1.6)"""
        if album_art_path and os.path.exists(album_art_path):
            try:
                bg = Image.open(album_art_path).convert("RGB")
                # Scale up to fill, then crop to exact card size
                bg_ratio = max(width / bg.width, height / bg.height) * 1.15
                new_w = int(bg.width * bg_ratio)
                new_h = int(bg.height * bg_ratio)
                bg = bg.resize((new_w, new_h), Image.LANCZOS)
                # Center crop
                left = (new_w - width) // 2
                top = (new_h - height) // 2
                bg = bg.crop((left, top, left + width, top + height))
                # Heavy blur
                bg = bg.filter(ImageFilter.GaussianBlur(radius=32 * self.scale))
                # Darken to ~30% brightness
                from PIL import ImageEnhance
                bg = ImageEnhance.Brightness(bg).enhance(0.3)
                # Boost saturation
                bg = ImageEnhance.Color(bg).enhance(1.6)
                return bg
            except Exception as e:
                print(f"Error creating album blur background: {e}")
        # Fallback: dark gray
        return Image.new("RGB", (width, height), (26, 26, 26))

    def _create_solid_bg(self, width, height, color):
        """Solid color background."""
        if isinstance(color, str):
            color = tuple(int(color.lstrip('#')[i:i+2], 16) for i in (0, 2, 4))
        return Image.new("RGB", (width, height), color)

    def _create_gradient_bg(self, width, height, colors):
        """3-color 135° diagonal gradient matching web app."""
        if not colors or len(colors) < 3:
            colors = ["#0f0c29", "#302b63", "#24243e"]
        
        rgb_colors = []
        for c in colors:
            if isinstance(c, str):
                rgb_colors.append(tuple(int(c.lstrip('#')[i:i+2], 16) for i in (0, 2, 4)))
            else:
                rgb_colors.append(c)
        
        c1, c2, c3 = rgb_colors
        img = Image.new("RGB", (width, height))
        pixels = img.load()
        
        for y in range(height):
            for x in range(width):
                # 135° diagonal: progress based on (x + y) / (w + h)
                t = (x + y) / max(1, width + height - 2)
                if t < 0.5:
                    # Blend c1 → c2
                    ratio = t * 2
                    r = int(c1[0] + (c2[0] - c1[0]) * ratio)
                    g = int(c1[1] + (c2[1] - c1[1]) * ratio)
                    b = int(c1[2] + (c2[2] - c1[2]) * ratio)
                else:
                    # Blend c2 → c3
                    ratio = (t - 0.5) * 2
                    r = int(c2[0] + (c3[0] - c2[0]) * ratio)
                    g = int(c2[1] + (c3[1] - c2[1]) * ratio)
                    b = int(c2[2] + (c3[2] - c2[2]) * ratio)
                pixels[x, y] = (r, g, b)
        
        return img

    # ── YouTube logo drawer ──────────────────────────────────────────

    def _draw_youtube_logo(self, draw, x, y, size, text_color):
        """Draw YouTube play-button: red circle with white triangle."""
        # Red circle
        draw.ellipse([(x, y), (x + size, y + size)], fill="#FF0000")
        # White triangle (play button) centered in the circle
        cx = x + size // 2
        cy = y + size // 2
        tri_h = int(size * 0.45)
        tri_w = int(size * 0.35)
        # Triangle points: right-pointing
        points = [
            (cx - tri_w // 2 + int(size * 0.05), cy - tri_h // 2),
            (cx - tri_w // 2 + int(size * 0.05), cy + tri_h // 2),
            (cx + tri_w // 2 + int(size * 0.05), cy),
        ]
        draw.polygon(points, fill="#FFFFFF")

    # ── Main card generator ──────────────────────────────────────────

    def generate_card(self, lyrics, song_title, artist, album_art_path=None,
                      text_color="#ffffff", output_path="lyric_card_yt.png",
                      bg_mode="albumblur", format="square",
                      solid_color="#1a1a1a", grad_colors=None):
        """Generate a YouTube Music style lyric card.
        
        Args:
            lyrics: str or list of lyric lines
            song_title: song name
            artist: artist name
            album_art_path: path to cover image (used for albumblur bg + thumbnail)
            text_color: "#ffffff" or "#111111"
            output_path: where to save
            bg_mode: "albumblur" | "solid" | "gradient"
            format: "square" | "portrait"
            solid_color: hex color for solid bg mode
            grad_colors: list of 3 hex colors for gradient bg mode
        """
        s = self.scale
        
        # Card dimensions based on format (matching web app: 420px square, 340px portrait)
        if format == "portrait":
            base_width = 340
        else:
            base_width = 420
        
        width = base_width * s
        padding = int(1.6 * 16 * s)  # 1.6rem = ~26px
        
        # Fonts
        font_title = self._get_font(self.font_bold, 14 * s, text=song_title)
        font_artist = self._get_font(self.font_regular, 12 * s, text=artist)
        font_lyrics = self._get_font(self.font_semibold, 21 * s, text=str(lyrics))
        font_footer = self._get_font(self.font_semibold, 10 * s)
        
        # Process lyrics
        max_text_width = width - (padding * 2)
        
        if isinstance(lyrics, str):
            lines = lyrics.split('\n')
        elif isinstance(lyrics, list):
            lines = list(lyrics)
        else:
            lines = []
        
        # Word-wrap lyrics
        lyric_lines_wrapped = []
        dummy_img = Image.new('RGB', (1, 1))
        draw_measure = ImageDraw.Draw(dummy_img)
        
        for line in lines:
            words = line.split()
            if not words:
                lyric_lines_wrapped.append("")
                continue
            current_line = words[0]
            for word in words[1:]:
                test_str = self._reshape(current_line + " " + word)
                bbox = draw_measure.textbbox((0, 0), test_str, font=font_lyrics)
                w = bbox[2] - bbox[0]
                if w <= max_text_width:
                    current_line += " " + word
                else:
                    lyric_lines_wrapped.append(current_line)
                    current_line = word
            lyric_lines_wrapped.append(current_line)
        
        # Calculate heights
        line_height = int(21 * s * 1.5)
        lyrics_block_height = len(lyric_lines_wrapped) * line_height
        
        thumb_size = 52 * s
        header_height = thumb_size
        gap_after_header = int(1.2 * 16 * s)  # 1.2rem gap
        gap_after_lyrics = int(1.2 * 16 * s)
        footer_height = 20 * s
        
        height = padding + header_height + gap_after_header + lyrics_block_height + gap_after_lyrics + footer_height + padding
        
        # 1. Create background
        if bg_mode == "solid":
            img = self._create_solid_bg(width, height, solid_color)
        elif bg_mode == "gradient":
            img = self._create_gradient_bg(width, height, grad_colors)
        else:  # albumblur (default)
            img = self._create_albumblur_bg(width, height, album_art_path)
        
        draw = ImageDraw.Draw(img)
        current_y = padding
        
        # 2. Header: thumbnail + song info
        album_radius = 8 * s
        
        if album_art_path and os.path.exists(album_art_path):
            try:
                album_img = Image.open(album_art_path).convert("RGBA")
                album_img = album_img.resize((thumb_size, thumb_size), Image.LANCZOS)
                mask = Image.new("L", (thumb_size, thumb_size), 0)
                mask_draw = ImageDraw.Draw(mask)
                mask_draw.rounded_rectangle([(0, 0), (thumb_size, thumb_size)], radius=album_radius, fill=255)
                album_img.putalpha(mask)
                img.paste(album_img, (padding, current_y), album_img)
            except Exception as e:
                print(f"Error loading album art: {e}")
                draw.rounded_rectangle([(padding, current_y), (padding + thumb_size, current_y + thumb_size)], radius=album_radius, fill=(100, 100, 100))
        else:
            draw.rounded_rectangle([(padding, current_y), (padding + thumb_size, current_y + thumb_size)], radius=album_radius, fill=(100, 100, 100))
        
        # Song info text
        text_x = padding + thumb_size + int(0.85 * 16 * s)  # 0.85rem gap
        
        reshaped_title = self._reshape(song_title)
        reshaped_artist = self._reshape(artist)
        
        title_bbox = draw.textbbox((0, 0), reshaped_title, font=font_title)
        title_h = title_bbox[3] - title_bbox[1]
        artist_bbox = draw.textbbox((0, 0), reshaped_artist, font=font_artist)
        artist_h = artist_bbox[3] - artist_bbox[1]
        
        title_artist_gap = 4 * s
        total_info_h = title_h + artist_h + title_artist_gap
        info_start_y = current_y + (thumb_size - total_info_h) // 2
        
        # Title text
        draw.text((text_x, info_start_y), reshaped_title, font=font_title, fill=text_color)
        
        # Artist text (60% opacity, matching web app rgba(255,255,255,.6))
        tc = tuple(int(text_color.lstrip('#')[i:i+2], 16) for i in (0, 2, 4))
        artist_tc = (*tc, int(255 * 0.6))
        overlay = Image.new("RGBA", img.size, (255, 255, 255, 0))
        overlay_draw = ImageDraw.Draw(overlay)
        overlay_draw.text((text_x, info_start_y + title_h + title_artist_gap), reshaped_artist, font=font_artist, fill=artist_tc)
        img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")
        draw = ImageDraw.Draw(img)
        
        # 3. Lyrics
        current_y += header_height + gap_after_header
        
        for line in lyric_lines_wrapped:
            reshaped_line = self._reshape(line)
            draw.text((padding, current_y), reshaped_line, font=font_lyrics, fill=text_color)
            current_y += line_height
        
        # 4. Footer: YouTube logo + "YouTube Music" text (bottom-right, matching web app)
        current_y = height - padding - footer_height
        
        logo_size = int(16 * s)
        
        # Measure footer text
        yt_line1 = "YouTube"
        yt_line2 = "Music"
        font_footer_small = self._get_font(self.font_semibold, 9 * s)
        
        l1_bbox = draw.textbbox((0, 0), yt_line1, font=font_footer_small)
        l1_w = l1_bbox[2] - l1_bbox[0]
        l2_bbox = draw.textbbox((0, 0), yt_line2, font=font_footer_small)
        l2_w = l2_bbox[2] - l2_bbox[0]
        label_w = max(l1_w, l2_w)
        
        gap = 5 * s
        total_footer_w = logo_size + gap + label_w
        
        # Right-align footer (matching web app justify-content: flex-end)
        footer_x = width - padding - total_footer_w
        logo_y = current_y + (footer_height - logo_size) // 2
        
        self._draw_youtube_logo(draw, footer_x, logo_y, logo_size, text_color)
        
        # Two-line label
        label_x = footer_x + logo_size + gap
        line1_y = logo_y - 1 * s
        line2_y = line1_y + 9 * s
        
        # 75% opacity text for footer (matching web app opacity: .75)
        footer_tc = (*tc, int(255 * 0.75))
        overlay2 = Image.new("RGBA", img.size, (255, 255, 255, 0))
        overlay2_draw = ImageDraw.Draw(overlay2)
        overlay2_draw.text((label_x, line1_y), yt_line1, font=font_footer_small, fill=footer_tc)
        overlay2_draw.text((label_x, line2_y), yt_line2, font=font_footer_small, fill=footer_tc)
        img = Image.alpha_composite(img.convert("RGBA"), overlay2).convert("RGB")
        draw = ImageDraw.Draw(img)
        
        # 5. Round the card corners (18px radius matching web app)
        final_radius = 18 * s
        mask = Image.new("L", img.size, 0)
        mask_draw = ImageDraw.Draw(mask)
        mask_draw.rounded_rectangle([(0, 0), img.size], radius=final_radius, fill=255)
        
        final_img = Image.new("RGBA", img.size, (0, 0, 0, 0))
        img.putalpha(mask)
        final_img.paste(img, (0, 0))
        
        final_img.save(output_path, format="PNG")
        return output_path


if __name__ == "__main__":
    pass
