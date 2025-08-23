import asyncio
import io
import logging
import tempfile
from pathlib import Path
from typing import Optional, List, Tuple, Dict
import json

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import requests

from models import LyricsData, VideoConfig, ProfileData
from config import settings
from llm_query_generator import generate_image_queries

logger = logging.getLogger(__name__)


class VideoGenerator:
    def __init__(self):
        self.temp_dir = Path(tempfile.gettempdir()) / "roastify_video"
        self.temp_dir.mkdir(exist_ok=True)
        
        # Video settings - OPTIMIZED FPS
        self.fps = 15  # Reduced from 30 for faster generation
        self.resolution = (1280, 720)  # 720p
        
        # Initialize OpenAI for DALL-E
        self.openai_client = None
        if settings.openai_api_key:
            import openai
            self.openai_client = openai.OpenAI(api_key=settings.openai_api_key)
    
    def _extract_key_words(self, lyrics: LyricsData) -> List[str]:
        """Extract key roast words and phrases from lyrics for text overlay"""
        key_words = []
        
        # Get all lyrics text
        full_text = lyrics.full_lyrics.lower()
        
        # Roast-specific words that should be emphasized
        roast_keywords = [
            'roast', 'fire', 'burn', 'flame', 'heat', 'savage', 'destroyed',
            'wrecked', 'demolished', 'obliterated', 'annihilated', 'toast',
            'fried', 'grilled', 'cooked', 'done', 'finished', 'owned'
        ]
        
        # Emphasis words
        emphasis_words = [
            'damn', 'yo', 'what', 'how', 'why', 'bruh', 'nah', 'stop',
            'dead', 'killed', 'slayed', 'facts', 'truth', 'real talk',
            'no cap', 'straight up', 'for real'
        ]
        
        # Professional roast terms
        professional_roasts = [
            'corporate', 'synergy', 'leverage', 'paradigm', 'buzzword',
            'networking', 'linkedin', 'influencer', 'thought leader',
            'entrepreneur', 'disrupt', 'innovate', 'scale', 'pivot'
        ]
        
        all_keywords = roast_keywords + emphasis_words + professional_roasts
        
        # Split lyrics into words
        words = full_text.replace('[', '').replace(']', '').split()
        
        # Find key words that appear in lyrics
        for word in words:
            clean_word = word.strip('.,!?()').lower()
            if clean_word in all_keywords:
                key_words.append(clean_word.upper())
        
        # Also extract phrases between quotes if any
        import re
        quoted_phrases = re.findall(r'"([^"]*)"', full_text)
        key_words.extend([phrase.upper() for phrase in quoted_phrases])
        
        # Remove duplicates while preserving order
        seen = set()
        unique_key_words = []
        for word in key_words:
            if word not in seen:
                seen.add(word)
                unique_key_words.append(word)
        
        # Limit to most impactful words (max 10-15 for video length)
        return unique_key_words[:15]
    
    async def generate_video(
        self,
        audio_bytes: bytes,
        lyrics: LyricsData,
        profile: ProfileData,
        config: VideoConfig,
        search_result: dict = None
    ) -> bytes:
        """Main entry point for video generation"""
        logger.info(f"Generating video for {profile.name}")
        
        # Fallback: create minimal search_result from ProfileData if not provided
        if search_result is None:
            search_result = {
                "url": profile.url or "",
                "platform": profile.platform or "unknown",
                "title": f"{profile.name} - Profile",
                "description": profile.bio or profile.raw_text[:200] or "No description available"
            }
            logger.info("Using fallback search_result created from ProfileData")
        
        try:
            # Step 1: Calculate video duration from audio
            audio_duration = await self._get_audio_duration(audio_bytes)
            config.duration = audio_duration
            
            # Step 2: Generate dynamic images (2 DALL-E + 1 Brave search)
            profile_images = await self._get_profile_images(profile, search_result)
            
            # Step 3: Generate video frames with dynamic images
            video_path = await self._create_video_frames(
                lyrics, profile, config, profile_images
            )
            
            # Step 4: Add audio to video
            final_video_bytes = await self._combine_audio_video(
                video_path, audio_bytes
            )
            
            return final_video_bytes
            
        except Exception as e:
            logger.error(f"Video generation failed: {e}")
            # Fallback: create simple static image video
            return await self._create_fallback_video(audio_bytes, profile, lyrics)
    
    async def _get_audio_duration(self, audio_bytes: bytes) -> float:
        """Get audio duration in seconds"""
        try:
            # Save audio to temp file to get duration
            temp_audio = self.temp_dir / "temp_audio.mp3"
            
            with open(temp_audio, 'wb') as f:
                f.write(audio_bytes)
            
            # Use cv2 to get duration (basic approach)
            # In production, use librosa or ffmpeg-python
            return 30.0  # Default 30 seconds, replace with actual duration detection
            
        except Exception as e:
            logger.warning(f"Could not get audio duration: {e}")
            return 30.0
    
    async def _get_profile_images(self, profile: ProfileData, search_result: dict) -> Dict[str, Optional[Image.Image]]:
        """Generate 3 dynamic images: 2 DALL-E + 1 Brave search"""
        images = {
            'dalle_roast_1': None,
            'dalle_roast_2': None,
            'brave_search': None
        }
        
        try:
            logger.info("Generating dynamic image queries...")
            # Generate contextual queries using LLM
            queries = await generate_image_queries(search_result)
            logger.info(f"Generated queries: {queries}")
            
            # Generate DALL-E images
            if self.openai_client:
                images['dalle_roast_1'] = await self._generate_dalle_image(queries['dalle_roast_1'])
                images['dalle_roast_2'] = await self._generate_dalle_image(queries['dalle_roast_2'])
            
            # Get Brave search image
            images['brave_search'] = await self._search_image_brave(queries['brave_search'])
            
            # Fill in fallbacks for any missing images
            for key, image in images.items():
                if image is None:
                    logger.warning(f"Using fallback for {key}")
                    images[key] = await self._create_avatar_placeholder(profile.name)
            
            return images
            
        except Exception as e:
            logger.warning(f"Failed to get dynamic images: {e}")
            # Return fallback images
            fallback = await self._create_avatar_placeholder(profile.name)
            return {
                'dalle_roast_1': fallback,
                'dalle_roast_2': fallback,
                'brave_search': fallback
            }
    
    def _extract_search_terms(self, profile: ProfileData) -> List[str]:
        """Extract search terms from profile for finding relevant images"""
        search_terms = []
        
        # Extract from bio/description
        bio_words = profile.bio.lower().split() if profile.bio else []
        
        # Look for company/profession keywords
        professional_keywords = [
            'ceo', 'founder', 'entrepreneur', 'developer', 'engineer', 
            'designer', 'manager', 'consultant', 'analyst', 'director'
        ]
        
        for keyword in professional_keywords:
            if keyword in ' '.join(bio_words):
                search_terms.append(f"{keyword} professional")
                break
        
        # Add generic professional terms if nothing specific found
        if not search_terms:
            search_terms.extend([
                "business professional",
                "office workspace", 
                "corporate background"
            ])
        
        return search_terms
    
    async def _search_image_brave(self, query: str) -> Optional[Image.Image]:
        """Search for images using Brave Search API"""
        try:
            if not settings.brave_api_key:
                logger.warning("No Brave API key found for image search")
                return None
            
            url = "https://api.search.brave.com/res/v1/images/search"
            headers = {
                "Accept": "application/json",
                "Accept-Encoding": "gzip",
                "X-Subscription-Token": settings.brave_api_key
            }
            
            params = {
                "q": query,
                "count": 5,  # Get a few options
                "search_lang": "en",
                "country": "US",
                "safesearch": "strict",
                "format": "json"
            }
            
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            
            data = response.json()
            results = data.get("results", [])
            
            # Try to download the first few images until one works
            for result in results[:3]:
                img_url = result.get("src")
                if img_url:
                    image = await self._download_image(img_url)
                    if image:
                        return image
            
            return None
            
        except Exception as e:
            logger.warning(f"Brave image search failed: {e}")
            return None
    
    async def _download_image(self, url: str) -> Optional[Image.Image]:
        """Download image from URL"""
        try:
            # Add user agent to avoid blocking
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            # Open image with PIL
            image = Image.open(io.BytesIO(response.content))
            
            # Convert to RGB if necessary
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Resize to reasonable size
            max_size = (800, 600)
            image.thumbnail(max_size, Image.Resampling.LANCZOS)
            
            return image
            
        except Exception as e:
            logger.warning(f"Failed to download image from {url}: {e}")
            return None
    
    async def _generate_dalle_image(self, prompt: str) -> Optional[Image.Image]:
        """Generate image using OpenAI DALL-E"""
        try:
            if not self.openai_client:
                logger.warning("No OpenAI client available for DALL-E")
                return None
            
            logger.info(f"Generating DALL-E image: {prompt[:50]}...")
            
            response = self.openai_client.images.generate(
                model="dall-e-3",
                prompt=prompt,
                size="1024x1024",
                quality="standard",
                n=1
            )
            
            # Download the generated image
            image_url = response.data[0].url
            image = await self._download_image(image_url)
            
            if image:
                logger.info("✅ DALL-E image generated successfully")
                return image
            else:
                logger.warning("❌ Failed to download DALL-E image")
                return None
                
        except Exception as e:
            logger.warning(f"DALL-E image generation failed: {e}")
            return None
    
    async def _create_avatar_placeholder(self, name: str) -> Image.Image:
        """Create a simple avatar with initials"""
        # Create 200x200 avatar with initials
        size = 200
        img = Image.new('RGB', (size, size), color=(70, 130, 180))  # Steel blue
        
        draw = ImageDraw.Draw(img)
        
        # Get initials
        initials = ''.join([word[0].upper() for word in name.split()[:2]])
        
        try:
            # Try to load a font
            font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 80)
        except:
            # Fallback to default font
            font = ImageFont.load_default()
        
        # Draw initials in center
        bbox = draw.textbbox((0, 0), initials, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        x = (size - text_width) // 2
        y = (size - text_height) // 2
        
        draw.text((x, y), initials, fill='white', font=font)
        
        # Make it circular
        mask = Image.new('L', (size, size), 0)
        mask_draw = ImageDraw.Draw(mask)
        mask_draw.ellipse((0, 0, size, size), fill=255)
        
        img.putalpha(mask)
        
        return img
    
    async def _create_video_frames(
        self,
        lyrics: LyricsData,
        profile: ProfileData,
        config: VideoConfig,
        profile_images: Dict[str, Optional[Image.Image]]
    ) -> Path:
        """Create video frames and render to file"""
        
        video_path = self.temp_dir / f"video_{profile.name.replace(' ', '_')}.mp4"
        
        # Initialize video writer
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(
            str(video_path),
            fourcc,
            self.fps,
            self.resolution
        )
        
        try:
            # Calculate timing
            total_frames = int(config.duration * self.fps)
            
            # Extract key words for emphasis
            key_words = self._extract_key_words(lyrics)
            logger.info(f"Extracted key words for emphasis: {key_words}")
            
            # Parse lyrics timing
            lyric_timings = self._parse_lyric_timings(lyrics)
            
            # Generate frames
            logger.info(f"Generating {total_frames} frames at {self.fps} FPS...")
            
            for frame_num in range(total_frames):
                # Progress logging every 15 frames
                if frame_num % 15 == 0:
                    progress = (frame_num / total_frames) * 100
                    logger.info(f"Progress: {frame_num}/{total_frames} frames ({progress:.1f}%)")
                
                timestamp = frame_num / self.fps
                
                # Select image based on new timeline: 0-5s bg, 5-25s images, 25s-end bg
                image_keys = list(profile_images.keys())
                current_image = None
                show_fullscreen = False
                
                if 5 <= timestamp < 25 and image_keys:
                    # Show images from 5-25s (20 second window)
                    image_window = timestamp - 5  # 0-20s within image window
                    seconds_per_image = 20 / len(image_keys)  # ~6.67s per image
                    image_index = int(image_window / seconds_per_image)
                    if image_index < len(image_keys):
                        current_image = profile_images[image_keys[image_index]]
                        show_fullscreen = True
                
                # Create frame
                frame = await self._create_frame(
                    timestamp, lyrics, profile, config, 
                    current_image, lyric_timings, key_words, show_fullscreen
                )
                
                # Convert PIL to OpenCV format
                cv_frame = cv2.cvtColor(np.array(frame), cv2.COLOR_RGB2BGR)
                out.write(cv_frame)
            
            out.release()
            return video_path
            
        except Exception as e:
            out.release()
            logger.error(f"Frame generation failed: {e}")
            raise
    
    def _parse_lyric_timings(self, lyrics: LyricsData) -> List[dict]:
        """Parse timing marks from lyrics"""
        if lyrics.timing_marks:
            return lyrics.timing_marks
        
        # Create basic timing from lyrics structure
        timings = []
        current_time = 0.0
        
        # Split lyrics into sections
        sections = lyrics.full_lyrics.split('\n\n')
        
        for section in sections:
            lines = [line.strip() for line in section.split('\n') if line.strip()]
            
            for line in lines:
                if line.startswith('[') and line.endswith(']'):
                    # Section header
                    timings.append({
                        'time': current_time,
                        'type': 'section',
                        'text': line,
                        'duration': 1.0
                    })
                    current_time += 1.0
                else:
                    # Lyric line
                    words = line.split()
                    duration = max(len(words) * 0.5, 2.0)  # 0.5s per word, min 2s
                    
                    timings.append({
                        'time': current_time,
                        'type': 'lyric',
                        'text': line,
                        'duration': duration
                    })
                    current_time += duration
        
        return timings
    
    async def _create_frame(
        self,
        timestamp: float,
        lyrics: LyricsData,
        profile: ProfileData,
        config: VideoConfig,
        profile_image: Optional[Image.Image],
        lyric_timings: List[dict],
        key_words: List[str] = None,
        show_fullscreen: bool = False
    ) -> Image.Image:
        """Create a single video frame"""
        
        # Create base frame
        frame = Image.new('RGB', self.resolution, color=(20, 20, 30))  # Dark background
        draw = ImageDraw.Draw(frame)
        
        # Add dynamic background effect
        frame = await self._add_background_effects(frame, timestamp, config)
        
        # Find current lyric
        current_lyric = self._get_current_lyric(timestamp, lyric_timings)
        
        # Add profile image (fullscreen or corner)
        if profile_image:
            if show_fullscreen:
                frame = await self._add_fullscreen_image(frame, profile_image, timestamp)
            else:
                frame = await self._add_profile_image(frame, profile_image, timestamp)
        
        # Add lyrics text with enhanced effects
        if current_lyric:
            frame = await self._add_lyric_text(
                frame, current_lyric, config, timestamp, key_words, show_fullscreen
            )
        
        # Add profile name (with transparency flag for fullscreen images)
        frame = await self._add_profile_name(frame, profile.name, show_fullscreen)
        
        # Add roast branding
        frame = await self._add_branding(frame, show_fullscreen)
        
        return frame
    
    def _get_current_lyric(self, timestamp: float, timings: List[dict]) -> Optional[str]:
        """Get the lyric that should be displayed at this timestamp"""
        current_lyric = None
        
        for timing in timings:
            start_time = timing['time']
            end_time = start_time + timing['duration']
            
            if start_time <= timestamp < end_time and timing['type'] == 'lyric':
                current_lyric = timing['text']
                break
        
        return current_lyric
    
    async def _add_background_effects(
        self, 
        frame: Image.Image, 
        timestamp: float, 
        config: VideoConfig
    ) -> Image.Image:
        """Add dynamic rap-style background effects"""
        
        width, height = frame.size
        draw = ImageDraw.Draw(frame)
        
        # Beat-synced effects (120 BPM)
        beat_interval = 60 / 120  # 0.5 seconds per beat
        beat_phase = (timestamp % beat_interval) / beat_interval
        
        # Dynamic color scheme
        if beat_phase < 0.1:  # Flash on beat
            # Bright flash colors
            bg_color1 = (60, 20, 80)   # Purple
            bg_color2 = (80, 60, 20)   # Orange
        else:
            # Base colors
            bg_color1 = (20, 20, 40)   # Dark blue
            bg_color2 = (40, 20, 20)   # Dark red
        
        # Create animated gradient background
        self._draw_animated_gradient(frame, bg_color1, bg_color2, timestamp)
        
        # Add pulsing circles on beat
        if beat_phase < 0.2:  # Pulse effect
            pulse_intensity = 1 - (beat_phase / 0.2)  # Fade out
            self._add_pulse_effects(draw, width, height, pulse_intensity, timestamp)
        
        # Add moving particles
        self._add_particle_effects(draw, width, height, timestamp)
        
        # Add scan lines for retro effect
        self._add_scan_lines(draw, width, height, timestamp)
        
        return frame
    
    def _draw_animated_gradient(self, frame: Image.Image, color1: tuple, color2: tuple, timestamp: float):
        """Draw animated gradient background - OPTIMIZED"""
        width, height = frame.size
        draw = ImageDraw.Draw(frame)
        
        # Use only 10 gradient steps instead of per-pixel
        gradient_steps = 10
        step_height = height // gradient_steps
        
        # Gradient offset changes with time
        offset = int(timestamp * 20) % height
        
        for i in range(gradient_steps + 1):  # +1 to fill remainder
            # Calculate gradient position
            gradient_pos = (i / gradient_steps + offset / height) % 1.0
            
            # Interpolate between colors
            r = int(color1[0] * (1 - gradient_pos) + color2[0] * gradient_pos)
            g = int(color1[1] * (1 - gradient_pos) + color2[1] * gradient_pos)
            b = int(color1[2] * (1 - gradient_pos) + color2[2] * gradient_pos)
            
            # Draw rectangle instead of line by line
            y1 = i * step_height
            y2 = min((i + 1) * step_height, height)
            draw.rectangle([(0, y1), (width, y2)], fill=(r, g, b))
    
    def _add_pulse_effects(self, draw, width: int, height: int, intensity: float, timestamp: float):
        """Add pulsing circular effects"""
        cx, cy = width // 2, height // 2
        
        # Multiple pulse rings
        for i in range(3):
            radius = int(100 * intensity * (i + 1))
            alpha = int(100 * intensity * (1 - i * 0.3))
            
            color = (255, 100, 150, alpha)  # Pink with alpha
            
            # Draw circle outline
            try:
                draw.ellipse(
                    [cx - radius, cy - radius, cx + radius, cy + radius],
                    outline=color[:3],
                    width=3
                )
            except:
                pass
    
    def _add_particle_effects(self, draw, width: int, height: int, timestamp: float):
        """Add moving particle effects"""
        import random
        
        # Seed for consistent animation
        random.seed(int(timestamp * 10))
        
        # Add floating particles - REDUCED
        for i in range(6):
            # Particle position moves over time
            base_x = random.randint(0, width)
            base_y = random.randint(0, height)
            
            # Add movement based on timestamp
            move_speed = 20
            x = int(base_x + timestamp * move_speed * random.uniform(-1, 1)) % width
            y = int(base_y + timestamp * move_speed * random.uniform(-1, 1)) % height
            
            # Particle size and color
            size = random.randint(1, 4)
            brightness = random.randint(100, 255)
            color = (brightness, brightness, brightness)
            
            # Draw particle
            draw.ellipse([x - size, y - size, x + size, y + size], fill=color)
    
    def _add_scan_lines(self, draw, width: int, height: int, timestamp: float):
        """Add retro scan line effects"""
        # Moving scan lines
        scan_speed = 50
        scan_offset = int(timestamp * scan_speed) % (height + 20)
        
        # Horizontal scan line
        for i in range(3):
            y = (scan_offset + i * 7) % height
            alpha = 100 - i * 30
            if alpha > 0:
                draw.line([(0, y), (width, y)], fill=(255, 255, 255, alpha), width=1)
        
        # Vertical scan lines (subtle)
        for x in range(0, width, 4):
            draw.line([(x, 0), (x, height)], fill=(255, 255, 255, 20), width=1)
    
    def _hsv_to_rgb(self, h: float, s: float, v: float) -> Tuple[int, int, int]:
        """Convert HSV to RGB"""
        h = h % 360
        c = v * s
        x = c * (1 - abs((h / 60) % 2 - 1))
        m = v - c
        
        if 0 <= h < 60:
            r, g, b = c, x, 0
        elif 60 <= h < 120:
            r, g, b = x, c, 0
        elif 120 <= h < 180:
            r, g, b = 0, c, x
        elif 180 <= h < 240:
            r, g, b = 0, x, c
        elif 240 <= h < 300:
            r, g, b = x, 0, c
        else:
            r, g, b = c, 0, x
        
        r = int((r + m) * 255)
        g = int((g + m) * 255)
        b = int((b + m) * 255)
        
        return (r, g, b)
    
    async def _add_profile_image(
        self, 
        frame: Image.Image, 
        profile_image: Image.Image, 
        timestamp: float
    ) -> Image.Image:
        """Add profile image with subtle animation"""
        
        # Resize profile image
        size = 150
        profile_resized = profile_image.resize((size, size), Image.Resampling.LANCZOS)
        
        # Position (top right)
        x = frame.width - size - 50
        y = 50
        
        # Subtle scale animation based on beat
        scale_factor = 1.0 + 0.05 * np.sin(timestamp * 3.14)  # Gentle pulsing
        if scale_factor != 1.0:
            new_size = int(size * scale_factor)
            profile_resized = profile_resized.resize((new_size, new_size), Image.Resampling.LANCZOS)
            x = frame.width - new_size - 50
            y = 50
        
        # Paste with alpha
        if profile_resized.mode == 'RGBA':
            frame.paste(profile_resized, (x, y), profile_resized)
        else:
            frame.paste(profile_resized, (x, y))
        
        return frame
    
    async def _add_fullscreen_image(
        self, 
        frame: Image.Image, 
        profile_image: Image.Image, 
        timestamp: float
    ) -> Image.Image:
        """Add profile image as fullscreen background with overlay effects"""
        
        # Resize image to fill the entire frame while maintaining aspect ratio
        frame_width, frame_height = frame.size
        img_width, img_height = profile_image.size
        
        # Calculate scaling to fill the frame (crop if needed)
        scale_x = frame_width / img_width
        scale_y = frame_height / img_height
        scale = max(scale_x, scale_y)  # Use max to fill the frame
        
        new_width = int(img_width * scale)
        new_height = int(img_height * scale)
        
        # Resize image
        scaled_image = profile_image.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        # Center the image (crop if larger than frame)
        x_offset = (frame_width - new_width) // 2
        y_offset = (frame_height - new_height) // 2
        
        # Create a copy of the scaled image to paste
        if scaled_image.mode != 'RGB':
            scaled_image = scaled_image.convert('RGB')
        
        # Crop if the image is larger than the frame
        if new_width > frame_width or new_height > frame_height:
            crop_x = max(0, -x_offset)
            crop_y = max(0, -y_offset)
            crop_width = min(new_width - crop_x, frame_width)
            crop_height = min(new_height - crop_y, frame_height)
            
            scaled_image = scaled_image.crop((crop_x, crop_y, crop_x + crop_width, crop_y + crop_height))
            x_offset = max(0, x_offset)
            y_offset = max(0, y_offset)
        
        # Paste the fullscreen image as background
        frame.paste(scaled_image, (x_offset, y_offset))
        
        # No overlay - let the image be fully visible
        
        return frame
    
    async def _add_lyric_text(
        self, 
        frame: Image.Image, 
        lyric_text: str, 
        config: VideoConfig,
        timestamp: float = 0,
        key_words: List[str] = None,
        is_fullscreen: bool = False
    ) -> Image.Image:
        """Add lyric text with exciting rap-style animations"""
        
        # Convert to RGBA for transparency support if using faint text
        if is_fullscreen and frame.mode != 'RGBA':
            frame = frame.convert('RGBA')
        
        draw = ImageDraw.Draw(frame)
        
        # Load fonts
        try:
            main_font_size = 52
            emphasis_font_size = 72
            main_font = ImageFont.truetype("/System/Library/Fonts/Arial Bold.ttf", main_font_size)
            emphasis_font = ImageFont.truetype("/System/Library/Fonts/Impact.ttf", emphasis_font_size)
        except:
            main_font = ImageFont.load_default()
            emphasis_font = ImageFont.load_default()
        
        # Check if this line contains key roast words
        words = lyric_text.split()
        has_key_words = any(word.upper().strip('.,!?()') in (key_words or []) for word in words)
        
        if has_key_words:
            # EMPHASIS MODE - Big, bold text with effects
            font = emphasis_font
            font_size = emphasis_font_size
            
            if not is_fullscreen:
                # Normal emphasis mode with full glow effects
                glow_color = (255, 100, 100)  # Red glow
                
                # Simple glow - only 4 directions
                glow_lines = self._wrap_text(lyric_text, font, frame.width - 200)
                total_height = len(glow_lines) * (font_size + 15)
                start_y = (frame.height - total_height) // 2
                
                # Draw glow in 4 directions only
                for dx, dy in [(-2, -2), (2, -2), (-2, 2), (2, 2)]:
                    for i, line in enumerate(glow_lines):
                        bbox = draw.textbbox((0, 0), line, font=font)
                        text_width = bbox[2] - bbox[0]
                        x = (frame.width - text_width) // 2
                        y = start_y + i * (font_size + 15)
                        
                        # Draw glow text
                        draw.text((x + dx, y + dy), line, fill=glow_color, font=font)
                
                # Main text color for emphasis
                text_color = (255, 255, 100)  # Bright yellow
                shadow_color = (255, 0, 0)    # Red shadow
            else:
                # Fullscreen mode: will use overlay transparency (handled below)
                text_color = (255, 255, 100)  # Bright yellow (will be made transparent via overlay)
                shadow_color = (255, 0, 0)    # Red shadow (will be made transparent via overlay)
            
        else:
            # NORMAL MODE - Regular styling
            font = main_font
            font_size = main_font_size
            # Use normal colors - transparency will be handled via overlay in fullscreen mode
            text_color = (255, 255, 255)  # White
            shadow_color = (0, 0, 0)      # Black shadow
        
        # Word wrap
        lines = self._wrap_text(lyric_text, font, frame.width - 200)
        
        # Position text
        total_height = len(lines) * (font_size + 15)
        
        # For emphasis text, move slightly higher for impact
        if has_key_words:
            start_y = (frame.height - total_height) // 2 - 50
        else:
            start_y = (frame.height - total_height) // 2
        
        for i, line in enumerate(lines):
            bbox = draw.textbbox((0, 0), line, font=font)
            text_width = bbox[2] - bbox[0]
            x = (frame.width - text_width) // 2
            y = start_y + i * (font_size + 15)
            
            # Add beat-sync shake effect for emphasis words
            if has_key_words and timestamp:
                # Shake based on beat (assuming 120 BPM)
                beat_interval = 60 / 120  # 0.5 seconds per beat
                beat_phase = (timestamp % beat_interval) / beat_interval
                if beat_phase < 0.1:  # Shake on beat
                    shake_x = int(5 * np.sin(timestamp * 20))
                    shake_y = int(3 * np.cos(timestamp * 25))
                    x += shake_x
                    y += shake_y
            
            # Add text shadow
            shadow_offset = 4 if has_key_words else 3
            
            if is_fullscreen:
                # Create text on separate overlay for true transparency
                text_overlay = Image.new('RGBA', frame.size, (0, 0, 0, 0))
                text_draw = ImageDraw.Draw(text_overlay)
                
                # Draw text with full opacity on overlay
                text_draw.text((x + shadow_offset, y + shadow_offset), line, fill=(0, 0, 0, 255), font=font)  # Shadow
                text_draw.text((x, y), line, fill=(255, 255, 255, 255), font=font)  # Main text
                
                # Apply overall transparency to the text overlay (10% opacity)
                transparent_overlay = Image.new('RGBA', frame.size, (0, 0, 0, 0))
                transparent_overlay = Image.blend(transparent_overlay, text_overlay, 0.1)  # 10% opacity
                
                # Composite onto frame
                if frame.mode != 'RGBA':
                    frame = frame.convert('RGBA')
                frame = Image.alpha_composite(frame, transparent_overlay)
            else:
                # Normal mode - draw text directly
                draw.text((x + shadow_offset, y + shadow_offset), line, fill=shadow_color, font=font)
                draw.text((x, y), line, fill=text_color, font=font)
            
            # Add sparkle effects for key words
            if has_key_words and timestamp and not is_fullscreen:
                self._add_sparkle_effects(draw, x, y, text_width, font_size, timestamp)
        
        # Convert back to RGB if we converted to RGBA
        if is_fullscreen and frame.mode == 'RGBA':
            frame = frame.convert('RGB')
        
        return frame
    
    def _wrap_text(self, text: str, font, max_width: int) -> List[str]:
        """Wrap text to fit within max_width"""
        draw = ImageDraw.Draw(Image.new('RGB', (1, 1)))  # Dummy image for text measurement
        words = text.split()
        lines = []
        current_line = []
        
        for word in words:
            test_line = ' '.join(current_line + [word])
            bbox = draw.textbbox((0, 0), test_line, font=font)
            if bbox[2] - bbox[0] > max_width:
                if current_line:
                    lines.append(' '.join(current_line))
                    current_line = [word]
                else:
                    lines.append(word)
            else:
                current_line.append(word)
        
        if current_line:
            lines.append(' '.join(current_line))
        
        return lines
    
    def _add_sparkle_effects(self, draw, x: int, y: int, width: int, height: int, timestamp: float):
        """Add sparkle effects around text"""
        import random
        
        # Seed random with timestamp for consistent but animated sparkles
        random.seed(int(timestamp * 10))
        
        sparkle_color = (255, 255, 255)
        
        # Add sparkles around the text
        for _ in range(6):
            sparkle_x = x + random.randint(-20, width + 20)
            sparkle_y = y + random.randint(-20, height + 20)
            
            # Draw simple sparkle (small cross)
            size = random.randint(2, 5)
            draw.line([sparkle_x - size, sparkle_y, sparkle_x + size, sparkle_y], fill=sparkle_color, width=2)
            draw.line([sparkle_x, sparkle_y - size, sparkle_x, sparkle_y + size], fill=sparkle_color, width=2)
    
    async def _add_profile_name(self, frame: Image.Image, name: str, is_fullscreen: bool = False) -> Image.Image:
        """Add profile name to frame"""
        
        # Convert to RGBA for transparency support
        if frame.mode != 'RGBA':
            frame = frame.convert('RGBA')
        
        # Create overlay for text
        overlay = Image.new('RGBA', frame.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)
        
        try:
            font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 32)
        except:
            font = ImageFont.load_default()
        
        # Position at top center
        bbox = draw.textbbox((0, 0), name, font=font)
        text_width = bbox[2] - bbox[0]
        x = (frame.width - text_width) // 2
        y = 30
        
        # Add background rectangle (no background during fullscreen images)
        if not is_fullscreen:
            # Normal mode: semi-transparent black background
            padding = 10
            rect_coords = [
                x - padding, y - padding,
                x + text_width + padding, y + (bbox[3] - bbox[1]) + padding
            ]
            draw.rectangle(rect_coords, fill=(0, 0, 0, 128))
            # Add main text with full opacity
            draw.text((x, y), name, fill=(255, 255, 255, 255), font=font)
        else:
            # Fullscreen mode: use overlay for true transparency
            # Apply overall transparency to the entire overlay (10% opacity)
            transparent_overlay = Image.new('RGBA', frame.size, (0, 0, 0, 0))
            transparent_draw = ImageDraw.Draw(transparent_overlay)
            transparent_draw.text((x, y), name, fill=(255, 255, 255, 255), font=font)
            
            # Blend with 10% opacity
            final_overlay = Image.blend(Image.new('RGBA', frame.size, (0, 0, 0, 0)), transparent_overlay, 0.1)
            overlay = Image.alpha_composite(overlay, final_overlay)
        
        # Composite overlay onto frame
        frame = Image.alpha_composite(frame, overlay)
        
        # Convert back to RGB
        frame = frame.convert('RGB')
        
        return frame
    
    async def _add_branding(self, frame: Image.Image, is_fullscreen: bool = False) -> Image.Image:
        """Add roastify branding"""
        
        draw = ImageDraw.Draw(frame)
        
        try:
            font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 24)
        except:
            font = ImageFont.load_default()
        
        branding_text = "🔥 ROASTIFY 🔥"
        
        # Position at bottom right
        bbox = draw.textbbox((0, 0), branding_text, font=font)
        text_width = bbox[2] - bbox[0]
        x = frame.width - text_width - 30
        y = frame.height - 50
        
        # Add text with shadow (faint during fullscreen)
        if is_fullscreen:
            # Convert to RGBA for transparency
            if frame.mode != 'RGBA':
                frame = frame.convert('RGBA')
            
            # Create text on separate overlay for true transparency
            brand_overlay = Image.new('RGBA', frame.size, (0, 0, 0, 0))
            brand_draw = ImageDraw.Draw(brand_overlay)
            brand_draw.text((x + 2, y + 2), branding_text, fill=(0, 0, 0, 255), font=font)  # Shadow
            brand_draw.text((x, y), branding_text, fill=(255, 100, 100, 255), font=font)  # Main text
            
            # Apply overall transparency (10% opacity)
            transparent_brand = Image.blend(Image.new('RGBA', frame.size, (0, 0, 0, 0)), brand_overlay, 0.1)
            frame = Image.alpha_composite(frame, transparent_brand)
            
            # Convert back to RGB
            frame = frame.convert('RGB')
        else:
            draw.text((x + 2, y + 2), branding_text, fill=(0, 0, 0), font=font)
            draw.text((x, y), branding_text, fill=(255, 100, 100), font=font)
        
        return frame
    
    async def _combine_audio_video(self, video_path: Path, audio_bytes: bytes) -> bytes:
        """Combine video with audio using ffmpeg"""
        
        try:
            # Save audio to temp file
            audio_path = self.temp_dir / "temp_audio.mp3"
            with open(audio_path, 'wb') as f:
                f.write(audio_bytes)
            
            # Output path
            output_path = self.temp_dir / "final_video.mp4"
            
            # Use subprocess to call ffmpeg
            import subprocess
            
            cmd = [
                'ffmpeg', '-y',  # Overwrite output
                '-i', str(video_path),  # Video input
                '-i', str(audio_path),  # Audio input
                '-c:v', 'libx264',  # Video codec
                '-c:a', 'aac',  # Audio codec
                '-strict', 'experimental',
                '-shortest',  # Match shortest stream
                str(output_path)
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                # Read final video
                with open(output_path, 'rb') as f:
                    return f.read()
            else:
                logger.error(f"FFmpeg failed: {result.stderr}")
                raise Exception("Video combination failed")
        
        except FileNotFoundError:
            logger.error("FFmpeg not found, creating video-only output")
            # Fallback: return video without audio
            with open(video_path, 'rb') as f:
                return f.read()
        except Exception as e:
            logger.error(f"Audio-video combination failed: {e}")
            # Fallback: return video without audio
            with open(video_path, 'rb') as f:
                return f.read()
    
    async def _create_fallback_video(
        self, 
        audio_bytes: bytes, 
        profile: ProfileData, 
        lyrics: LyricsData
    ) -> bytes:
        """Create simple fallback video"""
        
        logger.info("Creating fallback video")
        
        # Create simple static image video
        duration = 30.0  # 30 seconds
        total_frames = int(duration * self.fps)
        
        video_path = self.temp_dir / "fallback_video.mp4"
        
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(str(video_path), fourcc, self.fps, self.resolution)
        
        try:
            # Create static frame
            frame_img = Image.new('RGB', self.resolution, color=(30, 30, 50))
            draw = ImageDraw.Draw(frame_img)
            
            # Add text
            try:
                font = ImageFont.truetype("/System/Library/Fonts/Arial Bold.ttf", 60)
            except:
                font = ImageFont.load_default()
            
            text = f"🔥 ROASTING {profile.name.upper()} 🔥"
            bbox = draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            
            x = (self.resolution[0] - text_width) // 2
            y = self.resolution[1] // 2 - 50
            
            draw.text((x, y), text, fill=(255, 100, 100), font=font)
            
            # Convert to OpenCV format
            cv_frame = cv2.cvtColor(np.array(frame_img), cv2.COLOR_RGB2BGR)
            
            # Write frames
            for _ in range(total_frames):
                out.write(cv_frame)
            
            out.release()
            
            # Return video bytes
            with open(video_path, 'rb') as f:
                return f.read()
                
        except Exception as e:
            out.release()
            logger.error(f"Fallback video creation failed: {e}")
            
            # Ultimate fallback: return empty bytes
            return b""