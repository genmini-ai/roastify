#!/usr/bin/env python3
"""
Complete integration test for the full simplified Roastify pipeline

Tests the complete flow: LinkedIn URL → Scraper → Generator → Audio → Video

Usage:
    python test_full_pipeline.py --url https://linkedin.com/in/username
    python test_full_pipeline.py --url https://linkedin.com/in/username --style aggressive --voice nova
    python test_full_pipeline.py --url https://linkedin.com/in/username --skip-video --verbose
"""

import argparse
import asyncio
import json
import logging
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

# Add backend to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

# Test imports
from scraper import ProfileScraper
from generator import LyricsGenerator
from audio import AudioPipeline
from video import VideoGenerator
from models import LyricsData, AudioConfig, VideoConfig, ProfileData
from config import setup_logging

# Test configuration
TEST_OUTPUTS_DIR = Path(__file__).parent / "outputs"


class FullPipelineTester:
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.scraper = ProfileScraper()
        self.generator = LyricsGenerator()
        self.audio_pipeline = AudioPipeline()
        self.video_generator = VideoGenerator()
        self.test_outputs = TEST_OUTPUTS_DIR
        self.test_outputs.mkdir(exist_ok=True)
        
        # Setup logging
        level = logging.DEBUG if verbose else logging.INFO
        logging.basicConfig(level=level, format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)
    
    def check_api_availability(self) -> dict:
        """Check which APIs are available"""
        apis = {
            'brave': hasattr(self.scraper, 'scraper_settings') and bool(getattr(self.scraper.scraper_settings, 'brave_api_key', '')),
            'openai': self.generator.openai_client is not None,
            'anthropic': self.generator.anthropic_client is not None,
            'openai_audio': self.audio_pipeline.openai_client is not None
        }
        
        self.logger.info("🔑 API Availability Check:")
        for api, available in apis.items():
            status = "✅ Available" if available else "❌ Missing"
            self.logger.info(f"   {api}: {status}")
        
        return apis
    
    def search_result_to_profile(self, search_result: dict) -> ProfileData:
        """Convert search result dict to ProfileData for video generation"""
        title = search_result.get('title', 'Unknown Profile')
        name = title.split(' - ')[0].split(' | ')[0].strip()
        
        return ProfileData(
            url=search_result.get('url', ''),
            platform=search_result.get('platform', 'linkedin'),
            name=name,
            bio=search_result.get('description', ''),
            posts=[],
            work_history=[],
            education=[],
            skills=[],
            achievements=[],
            raw_text=f"Title: {title}\nDescription: {search_result.get('description', '')}"
        )
    
    async def test_full_pipeline(
        self,
        url: str,
        style: str = "playful",
        voice: str = "echo",
        beat_type: str = "trap",
        skip_video: bool = False,
        resolution: str = "1280x720"
    ) -> bool:
        """Test the complete pipeline from URL to final video"""
        
        if not url:
            self.logger.error("❌ No LinkedIn URL provided")
            return False
        
        self.logger.info("🚀 Starting COMPLETE Roastify pipeline test")
        self.logger.info(f"🔗 URL: {url}")
        self.logger.info(f"🎭 Style: {style}")
        self.logger.info(f"🎤 Voice: {voice}")
        self.logger.info(f"🥁 Beat: {beat_type}")
        self.logger.info(f"🎬 Video: {'Enabled' if not skip_video else 'Skipped'}")
        
        # Check APIs
        apis = self.check_api_availability()
        if not apis['brave']:
            self.logger.error("❌ BRAVE_API_KEY required for scraping")
            return False
        if not (apis['openai'] or apis['anthropic']):
            self.logger.error("❌ OpenAI or Anthropic API key required for lyrics")
            return False
        if not apis['openai_audio']:
            self.logger.error("❌ OpenAI API key required for TTS audio generation")
            return False
        
        try:
            overall_start = time.time()
            
            # ========================================
            # STEP 1: SCRAPING
            # ========================================
            self.logger.info("\n" + "="*60)
            self.logger.info("STEP 1: 📊 SCRAPING LINKEDIN PROFILE")
            self.logger.info("="*60)
            
            scrape_start = time.time()
            search_result = await self.scraper.scrape_profile_simple(url)
            scrape_duration = time.time() - scrape_start
            
            if "error" in search_result:
                self.logger.error(f"❌ Scraping failed: {search_result.get('error')}")
                return False
            
            self.logger.info(f"✅ Scraping completed in {scrape_duration:.2f}s")
            self.logger.info(f"📄 Title: {search_result.get('title', 'No title')}")
            self.logger.info(f"📝 Description: {search_result.get('description', 'No description')[:100]}...")
            
            # ========================================
            # STEP 2: LYRICS GENERATION
            # ========================================
            self.logger.info("\n" + "="*60)
            self.logger.info("STEP 2: 🎤 GENERATING RAP LYRICS")
            self.logger.info("="*60)
            
            gen_start = time.time()
            lyrics = await self.generator.generate_lyrics_from_search(search_result, style)
            gen_duration = time.time() - gen_start
            
            if not lyrics:
                self.logger.error("❌ Lyrics generation failed")
                return False
            
            self.logger.info(f"✅ Lyrics generation completed in {gen_duration:.2f}s")
            self.logger.info(f"🎵 Generated {len(lyrics.verses)} verse(s)")
            self.logger.info(f"🎯 Style: {lyrics.style}, BPM: {lyrics.bpm}")
            
            # Show sample lyrics
            if lyrics.intro:
                self.logger.info(f"\n🎤 SAMPLE LYRICS PREVIEW:")
                self.logger.info("─" * 40)
                self.logger.info(f"[INTRO] {lyrics.intro[:100]}...")
                if lyrics.verses and lyrics.verses[0]:
                    self.logger.info(f"[VERSE] {lyrics.verses[0][:100]}...")
                self.logger.info("─" * 40)
            
            # ========================================
            # STEP 3: AUDIO GENERATION
            # ========================================
            self.logger.info("\n" + "="*60)
            self.logger.info("STEP 3: 🎵 GENERATING AUDIO (TTS + BEAT)")
            self.logger.info("="*60)
            
            audio_start = time.time()
            
            # Create audio config
            audio_config = AudioConfig(
                voice_model=voice,
                speed=1.1,
                pitch_shift=0.0,
                autotune_strength=0.7,
                reverb_level=0.3,
                compression_ratio=4.0,
                beat_type=beat_type,
                target_bpm=lyrics.bpm
            )
            
            audio_bytes = await self.audio_pipeline.generate_audio(lyrics, audio_config)
            audio_duration = time.time() - audio_start
            
            if not audio_bytes:
                self.logger.error("❌ Audio generation failed")
                return False
            
            self.logger.info(f"✅ Audio generation completed in {audio_duration:.2f}s")
            self.logger.info(f"🎵 Audio size: {len(audio_bytes):,} bytes")
            self.logger.info(f"🎧 Voice: {voice}, Beat: {beat_type}")
            
            video_bytes = None
            video_duration = 0
            
            # ========================================
            # STEP 4: VIDEO GENERATION (Optional)
            # ========================================
            if not skip_video:
                self.logger.info("\n" + "="*60)
                self.logger.info("STEP 4: 🎬 GENERATING VIDEO WITH LYRICS")
                self.logger.info("="*60)
                
                video_start = time.time()
                
                # Convert search result to ProfileData for video
                profile = self.search_result_to_profile(search_result)
                
                # Create video config
                video_config = VideoConfig(
                    resolution=resolution,
                    fps=30,
                    duration=None,  # Auto-detected from audio
                    lyric_style="modern",
                    background_style="dynamic",
                    include_profile_image=False,  # Skip for testing
                    effects_intensity=0.7
                )
                
                video_bytes = await self.video_generator.generate_video(
                    audio_bytes, lyrics, profile, video_config
                )
                video_duration = time.time() - video_start
                
                if not video_bytes:
                    self.logger.error("❌ Video generation failed")
                    return False
                
                self.logger.info(f"✅ Video generation completed in {video_duration:.2f}s")
                self.logger.info(f"🎬 Video size: {len(video_bytes):,} bytes")
                self.logger.info(f"📺 Resolution: {resolution}")
            
            # ========================================
            # STEP 5: SAVE ALL OUTPUTS
            # ========================================
            self.logger.info("\n" + "="*60)
            self.logger.info("STEP 5: 💾 SAVING ALL OUTPUTS")
            self.logger.info("="*60)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Extract name for filenames
            name = search_result.get('title', 'unknown').split(' - ')[0].split(' | ')[0].strip()
            safe_name = "".join(c for c in name if c.isalnum() or c in (' ', '-', '_')).rstrip()
            safe_name = safe_name.replace(' ', '_').lower()[:20]
            
            # Save files
            files_saved = []
            
            # 1. Complete pipeline results (JSON)
            pipeline_file = self.test_outputs / f"full_pipeline_{safe_name}_{timestamp}.json"
            with open(pipeline_file, 'w') as f:
                json.dump({
                    'url': url,
                    'style': style,
                    'voice': voice,
                    'beat_type': beat_type,
                    'skip_video': skip_video,
                    'durations': {
                        'scraping': scrape_duration,
                        'lyrics_generation': gen_duration,
                        'audio_generation': audio_duration,
                        'video_generation': video_duration,
                        'total': time.time() - overall_start
                    },
                    'search_result': search_result,
                    'lyrics': lyrics.model_dump(mode='json'),
                    'audio_size': len(audio_bytes),
                    'video_size': len(video_bytes) if video_bytes else 0,
                    'timestamp': datetime.now().isoformat()
                }, f, indent=2)
            files_saved.append(str(pipeline_file))
            
            # 2. Formatted lyrics (TXT)
            lyrics_file = self.test_outputs / f"full_pipeline_lyrics_{safe_name}_{timestamp}.txt"
            with open(lyrics_file, 'w') as f:
                f.write(f"ROAST RAP FOR: {search_result.get('title', 'Unknown')}\n")
                f.write(f"URL: {url}\n")
                f.write(f"Style: {style}\n")
                f.write(f"Generated: {datetime.now().isoformat()}\n")
                f.write("="*60 + "\n\n")
                f.write(lyrics.full_lyrics)
            files_saved.append(str(lyrics_file))
            
            # 3. Audio file (MP3)
            audio_file = self.test_outputs / f"full_pipeline_audio_{safe_name}_{timestamp}.mp3"
            with open(audio_file, 'wb') as f:
                f.write(audio_bytes)
            files_saved.append(str(audio_file))
            
            # 4. Video file (MP4) if generated
            if video_bytes:
                video_file = self.test_outputs / f"full_pipeline_video_{safe_name}_{timestamp}.mp4"
                with open(video_file, 'wb') as f:
                    f.write(video_bytes)
                files_saved.append(str(video_file))
            
            # ========================================
            # FINAL SUMMARY
            # ========================================
            total_duration = time.time() - overall_start
            
            self.logger.info("\n" + "🎉"*20)
            self.logger.info("🎉 FULL PIPELINE COMPLETED SUCCESSFULLY!")
            self.logger.info("🎉"*20)
            
            self.logger.info(f"\n⏱️  TIMING BREAKDOWN:")
            self.logger.info(f"   📊 Scraping: {scrape_duration:.2f}s")
            self.logger.info(f"   🎤 Lyrics: {gen_duration:.2f}s")
            self.logger.info(f"   🎵 Audio: {audio_duration:.2f}s")
            if video_duration > 0:
                self.logger.info(f"   🎬 Video: {video_duration:.2f}s")
            self.logger.info(f"   🏁 TOTAL: {total_duration:.2f}s")
            
            self.logger.info(f"\n📁 FILES GENERATED:")
            for file_path in files_saved:
                self.logger.info(f"   ✅ {Path(file_path).name}")
            
            self.logger.info(f"\n🎯 TARGET: {search_result.get('title', 'Unknown')}")
            self.logger.info(f"🎭 STYLE: {style}")
            self.logger.info(f"🎤 VOICE: {voice}")
            self.logger.info(f"🥁 BEAT: {beat_type}")
            
            if video_bytes:
                self.logger.info(f"\n🎬 FINAL VIDEO: {Path(video_file).name}")
                self.logger.info(f"📺 Resolution: {resolution}")
                self.logger.info(f"💾 Size: {len(video_bytes):,} bytes")
            else:
                self.logger.info(f"\n🎵 FINAL AUDIO: {Path(audio_file).name}")
                self.logger.info(f"💾 Size: {len(audio_bytes):,} bytes")
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Pipeline failed: {e}")
            if self.verbose:
                import traceback
                traceback.print_exc()
            return False


async def main():
    """Main test function"""
    parser = argparse.ArgumentParser(description="Test complete Roastify pipeline (URL → Video)")
    
    parser.add_argument('--url', required=True, help='LinkedIn URL to roast')
    parser.add_argument('--style', choices=['aggressive', 'playful', 'witty'], default='playful', 
                       help='Roast style')
    parser.add_argument('--voice', choices=['echo', 'alloy', 'nova', 'shimmer'], default='echo',
                       help='TTS voice')
    parser.add_argument('--beat', choices=['trap', 'boom_bap', 'lofi'], default='trap',
                       help='Beat type')
    parser.add_argument('--resolution', choices=['1280x720', '1920x1080', '640x360'], 
                       default='1280x720', help='Video resolution')
    parser.add_argument('--skip-video', action='store_true', 
                       help='Skip video generation (audio only)')
    parser.add_argument('--verbose', action='store_true', help='Verbose output')
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging()
    
    tester = FullPipelineTester(verbose=args.verbose)
    
    try:
        success = await tester.test_full_pipeline(
            url=args.url,
            style=args.style,
            voice=args.voice,
            beat_type=args.beat,
            skip_video=args.skip_video,
            resolution=args.resolution
        )
        
        if success:
            print("\n🎉 COMPLETE PIPELINE TEST SUCCESSFUL!")
            print("📁 Check the outputs folder for your generated roast!")
            if not args.skip_video:
                print("🎬 Your roast video is ready!")
        else:
            print("\n❌ Pipeline test failed - check logs above")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n⚠️  Pipeline interrupted by user")
    except Exception as e:
        print(f"\n❌ Pipeline failed with error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())