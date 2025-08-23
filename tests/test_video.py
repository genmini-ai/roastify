#!/usr/bin/env python3
"""
Test module for simplified video generation pipeline

Tests video generation from generated audio and lyrics.

Usage:
    python test_video.py --audio-file outputs/roast_audio_echo_trap_20250823_100007.mp3 --lyrics-file outputs/simple_pipeline_20250823_100007.json
    python test_video.py --test creation --verbose
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
from models import LyricsData, VideoConfig, ProfileData
from video import VideoGenerator
from config import setup_logging

# Test configuration
TEST_OUTPUTS_DIR = Path(__file__).parent / "outputs"


class VideoTester:
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.video_generator = VideoGenerator()
        self.test_outputs = TEST_OUTPUTS_DIR
        self.test_outputs.mkdir(exist_ok=True)
        
        # Setup logging
        level = logging.DEBUG if verbose else logging.INFO
        logging.basicConfig(level=level, format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)
    
    def load_audio_file(self, file_path: str) -> Optional[bytes]:
        """Load audio file as bytes"""
        try:
            with open(file_path, 'rb') as f:
                audio_bytes = f.read()
            
            self.logger.info(f"✅ Loaded audio file: {file_path}")
            self.logger.info(f"🎵 Audio size: {len(audio_bytes):,} bytes")
            return audio_bytes
            
        except Exception as e:
            self.logger.error(f"❌ Failed to load audio: {e}")
            return None
    
    def load_lyrics_from_file(self, file_path: str) -> Optional[tuple]:
        """Load lyrics and search result from generated JSON file"""
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            lyrics_data = data.get('lyrics')
            search_result = data.get('search_result')
            
            if not lyrics_data:
                self.logger.error("No lyrics found in file")
                return None
            
            # Convert to LyricsData object
            lyrics = LyricsData(**lyrics_data)
            
            self.logger.info(f"✅ Loaded lyrics from {file_path}")
            self.logger.info(f"🎵 Style: {lyrics.style}, BPM: {lyrics.bpm}")
            
            return lyrics, search_result
            
        except Exception as e:
            self.logger.error(f"❌ Failed to load lyrics: {e}")
            return None
    
    def search_result_to_profile(self, search_result: dict) -> ProfileData:
        """Convert search result dict to ProfileData for video generation"""
        
        # Extract name from title
        title = search_result.get('title', 'Unknown Profile')
        name = title.split(' - ')[0].split(' | ')[0].strip()
        
        # Create ProfileData from search result
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
    
    def create_sample_data(self) -> tuple:
        """Create sample audio, lyrics, and profile for testing"""
        
        # Create sample audio bytes (empty for testing structure)
        sample_audio = b"sample_audio_data"  # In real use, this would be actual MP3 data
        
        # Create sample lyrics
        sample_lyrics = LyricsData(
            intro="Yo, check it, we got a test profile in the building\nTime to roast this video test\nGot your data right here on the screen\nLet's see what this video means",
            verses=[
                "Testing video generation with our sample flow\nMaking sure the lyrics sync and the visuals show\nFrom audio bytes to video frames complete\nThis roast video can't be beat"
            ],
            hook="Test User, Test User, what's the video about?\nLyrics synced with visuals, no doubt\nFrom scraping to audio to video complete\nThis pipeline makes the roast sweet",
            outro="That's a wrap on this video test session\nHope the rendering made a good impression\nFrom code to video, the pipeline flows\nThat's how our roast video generation goes",
            rhyme_scheme="AABB",
            bpm=90,
            style="playful",
            wordplay_rating=0.7,
            full_lyrics="[INTRO] Yo, check it...\n[VERSE] Testing video...\n[HOOK] Test User...\n[OUTRO] That's a wrap...",
            timing_marks=[]
        )
        
        # Create sample search result
        sample_search_result = {
            'url': 'https://linkedin.com/in/test-profile',
            'platform': 'linkedin',
            'title': 'Test User - Software Engineer | LinkedIn',
            'description': 'Passionate about testing and video generation. Building automated pipelines for creative content.'
        }
        
        return sample_audio, sample_lyrics, sample_search_result
    
    async def test_video_generation(
        self, 
        audio_bytes: bytes,
        lyrics: LyricsData,
        search_result: dict,
        resolution: str = "1280x720"
    ) -> bool:
        """Test video generation with given inputs"""
        
        self.logger.info(f"🎬 Testing video generation at {resolution} resolution")
        self.logger.info(f"🎵 Audio size: {len(audio_bytes):,} bytes")
        self.logger.info(f"📄 Target: {search_result.get('title', 'Unknown')}")
        
        try:
            start_time = time.time()
            
            # Convert search result to ProfileData for video generator
            profile = self.search_result_to_profile(search_result)
            
            # Create video config
            video_config = VideoConfig(
                resolution=resolution,
                fps=30,
                duration=None,  # Auto-detected from audio
                lyric_style="modern",
                background_style="dynamic",
                include_profile_image=False,  # Skip image download for testing
                effects_intensity=0.7
            )
            
            # Generate video
            self.logger.info("🎬 Generating video with lyrics overlay...")
            video_bytes = await self.video_generator.generate_video(
                audio_bytes, lyrics, profile, video_config, search_result
            )
            
            duration = time.time() - start_time
            
            if not video_bytes:
                self.logger.error("❌ Video generation failed - no bytes returned")
                return False
            
            # Save video
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            video_file = self.test_outputs / f"roast_video_{resolution.replace('x', 'p')}_{timestamp}.mp4"
            
            with open(video_file, 'wb') as f:
                f.write(video_bytes)
            
            # Save metadata
            metadata_file = self.test_outputs / f"video_metadata_{timestamp}.json"
            with open(metadata_file, 'w') as f:
                json.dump({
                    'video_file': str(video_file),
                    'generation_time': duration,
                    'video_size': len(video_bytes),
                    'audio_size': len(audio_bytes),
                    'config': video_config.model_dump(mode='json'),
                    'profile_info': {
                        'name': profile.name,
                        'platform': profile.platform,
                        'title': search_result.get('title', '')
                    },
                    'lyrics_info': {
                        'style': lyrics.style,
                        'bpm': lyrics.bpm,
                        'verse_count': len(lyrics.verses)
                    },
                    'timestamp': datetime.now().isoformat()
                }, f, indent=2)
            
            # Results
            self.logger.info(f"✅ Video generation completed in {duration:.2f}s")
            self.logger.info(f"🎬 Video size: {len(video_bytes):,} bytes")
            self.logger.info(f"📁 Video saved: {video_file}")
            self.logger.info(f"📄 Metadata saved: {metadata_file}")
            
            # Video details
            self.logger.info("\n🎬 VIDEO DETAILS:")
            self.logger.info("=" * 50)
            self.logger.info(f"Resolution: {resolution}")
            self.logger.info(f"FPS: {video_config.fps}")
            self.logger.info(f"Profile: {profile.name}")
            self.logger.info(f"Style: {lyrics.style}")
            self.logger.info(f"Duration: {video_config.duration or 'Auto-detected'}")
            self.logger.info("=" * 50)
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Video generation failed: {e}")
            if self.verbose:
                import traceback
                traceback.print_exc()
            return False
    
    async def test_different_resolutions(
        self, 
        audio_bytes: bytes, 
        lyrics: LyricsData, 
        search_result: dict
    ) -> bool:
        """Test video generation with different resolutions"""
        resolutions = ["1280x720", "1920x1080", "640x360"]
        self.logger.info(f"📺 Testing different resolutions: {resolutions}")
        
        results = {}
        for resolution in resolutions:
            self.logger.info(f"\n--- Testing {resolution} resolution ---")
            results[resolution] = await self.test_video_generation(
                audio_bytes, lyrics, search_result, resolution
            )
        
        # Summary
        passed = sum(results.values())
        total = len(results)
        
        self.logger.info(f"\n📊 Resolution Test Results: {passed}/{total} passed")
        for resolution, result in results.items():
            status = "✅" if result else "❌"
            self.logger.info(f"   {status} {resolution}")
        
        return all(results.values())
    
    async def run_all_tests(
        self, 
        audio_bytes: bytes, 
        lyrics: LyricsData, 
        search_result: dict
    ) -> bool:
        """Run comprehensive video tests"""
        self.logger.info("🚀 Running all video tests")
        
        results = {}
        
        # Test 1: Basic generation
        self.logger.info("\n" + "="*60)
        self.logger.info("TEST 1: Basic Video Generation")
        self.logger.info("="*60)
        results['basic'] = await self.test_video_generation(audio_bytes, lyrics, search_result)
        
        # Test 2: Different resolutions  
        self.logger.info("\n" + "="*60)
        self.logger.info("TEST 2: Different Resolutions")
        self.logger.info("="*60)
        results['resolutions'] = await self.test_different_resolutions(audio_bytes, lyrics, search_result)
        
        # Summary
        passed = sum(results.values())
        total = len(results)
        
        self.logger.info("\n" + "="*60)
        self.logger.info(f"📊 OVERALL RESULTS: {passed}/{total} test categories passed")
        self.logger.info("="*60)
        
        for test_name, result in results.items():
            status = "✅" if result else "❌"
            self.logger.info(f"   {status} {test_name}")
        
        return all(results.values())


async def main():
    """Main test function"""
    parser = argparse.ArgumentParser(description="Test video generation from audio and lyrics")
    
    parser.add_argument('--audio-file', help='Audio file (MP3) to use for video')
    parser.add_argument('--lyrics-file', help='JSON file with generated lyrics')
    parser.add_argument('--resolution', choices=['1280x720', '1920x1080', '640x360'], 
                       default='1280x720', help='Video resolution')
    parser.add_argument('--test', choices=['single', 'resolutions', 'all'], 
                       default='single', help='Test to run')
    parser.add_argument('--verbose', action='store_true', help='Verbose output')
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging()
    
    tester = VideoTester(verbose=args.verbose)
    
    # Load or create test data
    if args.audio_file and args.lyrics_file:
        # Load real data
        audio_bytes = tester.load_audio_file(args.audio_file)
        lyrics_data = tester.load_lyrics_from_file(args.lyrics_file)
        
        if not audio_bytes:
            print("❌ Failed to load audio file")
            sys.exit(1)
        if not lyrics_data:
            print("❌ Failed to load lyrics file")
            sys.exit(1)
            
        lyrics, search_result = lyrics_data
        
    else:
        # Use sample data
        print("⚠️  No files provided, using sample data for structure testing")
        audio_bytes, lyrics, search_result = tester.create_sample_data()
    
    try:
        if args.test == 'single':
            success = await tester.test_video_generation(
                audio_bytes, lyrics, search_result, resolution=args.resolution
            )
            
        elif args.test == 'resolutions':
            success = await tester.test_different_resolutions(audio_bytes, lyrics, search_result)
            
        elif args.test == 'all':
            success = await tester.run_all_tests(audio_bytes, lyrics, search_result)
        
        if success:
            print(f"\n🎉 Video test {'completed successfully' if success else 'failed'}!")
            print("🎬 Check the outputs folder for generated video files!")
        else:
            print("\n❌ Video tests failed - check logs above")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n⚠️  Tests interrupted by user")
    except Exception as e:
        print(f"\n❌ Tests failed with error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())