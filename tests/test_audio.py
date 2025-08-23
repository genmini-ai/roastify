#!/usr/bin/env python3
"""
Test module for simplified audio synthesis pipeline

Tests audio generation from generated lyrics using OpenAI TTS and audio processing.

Usage:
    python test_audio.py --lyrics-file outputs/simple_pipeline_20250823_100007.json
    python test_audio.py --voice echo --verbose
    python test_audio.py --test tts
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
from models import LyricsData, AudioConfig
from audio import AudioPipeline
from config import setup_logging

# Test configuration
TEST_OUTPUTS_DIR = Path(__file__).parent / "outputs"


class AudioTester:
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.audio_pipeline = AudioPipeline()
        self.test_outputs = TEST_OUTPUTS_DIR
        self.test_outputs.mkdir(exist_ok=True)
        
        # Setup logging
        level = logging.DEBUG if verbose else logging.INFO
        logging.basicConfig(level=level, format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)
    
    def load_lyrics_from_file(self, file_path: str) -> Optional[LyricsData]:
        """Load lyrics from generated JSON file"""
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            lyrics_data = data.get('lyrics')
            if not lyrics_data:
                self.logger.error("No lyrics found in file")
                return None
            
            # Convert to LyricsData object
            lyrics = LyricsData(**lyrics_data)
            self.logger.info(f"✅ Loaded lyrics from {file_path}")
            self.logger.info(f"🎵 Style: {lyrics.style}, BPM: {lyrics.bpm}")
            return lyrics
            
        except Exception as e:
            self.logger.error(f"❌ Failed to load lyrics: {e}")
            return None
    
    def create_sample_lyrics(self) -> LyricsData:
        """Create sample lyrics for testing when no file is provided"""
        return LyricsData(
            intro="Yo, check it, we got a test profile in the building\nTime to roast this sample data\nGot your LinkedIn right here on the screen\nLet's break down what this really means",
            verses=[
                "Posted up thinking you run the corporate game\nBut your profile's got us laughing all the same\nTalking bout synergy and innovation\nBuzzword champion of the corporation",
                "LinkedIn influencer with the fake inspiration\nTime to bring you back down to your station\nYour bio reads like a robot wrote it\nProfessional headshot but we're not sold on it"
            ],
            hook="Test User, Test User, what you really about?\nAll these buzzwords but we got you figured out\nProfessional network but you're just like the rest\nTime to put your corporate speak to the test",
            outro="That's a wrap on this testing session\nHope you learned a valuable lesson\nKeep it real, drop the corporate facade\nThis has been your friendly test squad",
            rhyme_scheme="AABB",
            bpm=90,
            style="playful",
            wordplay_rating=0.7,
            full_lyrics="[INTRO] Yo, check it...\n[VERSE] Posted up...\n[HOOK] Test User...\n[OUTRO] That's a wrap...",
            timing_marks=[]
        )
    
    async def test_audio_generation(
        self, 
        lyrics: LyricsData, 
        voice: str = "echo",
        beat_type: str = "trap"
    ) -> bool:
        """Test audio generation with given lyrics"""
        
        self.logger.info(f"🎤 Testing audio generation with {voice} voice and {beat_type} beat")
        self.logger.info(f"📄 Lyrics style: {lyrics.style}, BPM: {lyrics.bpm}")
        
        try:
            start_time = time.time()
            
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
            
            # Generate audio
            self.logger.info("🎵 Generating audio with TTS and beat...")
            audio_bytes = await self.audio_pipeline.generate_audio(lyrics, audio_config)
            
            duration = time.time() - start_time
            
            if not audio_bytes:
                self.logger.error("❌ Audio generation failed - no bytes returned")
                return False
            
            # Save audio
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            audio_file = self.test_outputs / f"roast_audio_{voice}_{beat_type}_{timestamp}.mp3"
            
            with open(audio_file, 'wb') as f:
                f.write(audio_bytes)
            
            # Save metadata
            metadata_file = self.test_outputs / f"audio_metadata_{timestamp}.json"
            with open(metadata_file, 'w') as f:
                json.dump({
                    'audio_file': str(audio_file),
                    'generation_time': duration,
                    'audio_size': len(audio_bytes),
                    'config': audio_config.model_dump(mode='json'),
                    'lyrics_info': {
                        'style': lyrics.style,
                        'bpm': lyrics.bpm,
                        'verse_count': len(lyrics.verses)
                    },
                    'timestamp': datetime.now().isoformat()
                }, f, indent=2)
            
            # Results
            self.logger.info(f"✅ Audio generation completed in {duration:.2f}s")
            self.logger.info(f"🎵 Audio size: {len(audio_bytes):,} bytes")
            self.logger.info(f"📁 Audio saved: {audio_file}")
            self.logger.info(f"📄 Metadata saved: {metadata_file}")
            
            # Play sample info
            self.logger.info("\n🎧 AUDIO DETAILS:")
            self.logger.info("=" * 50)
            self.logger.info(f"Voice: {voice}")
            self.logger.info(f"Beat: {beat_type}")
            self.logger.info(f"BPM: {lyrics.bpm}")
            self.logger.info(f"Duration: ~{len(lyrics.full_lyrics.split())/200*60:.1f} seconds (estimated)")
            self.logger.info("=" * 50)
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Audio generation failed: {e}")
            if self.verbose:
                import traceback
                traceback.print_exc()
            return False
    
    async def test_different_voices(self, lyrics: LyricsData) -> bool:
        """Test audio generation with different TTS voices"""
        voices = ["echo", "alloy", "nova", "shimmer"]
        self.logger.info(f"🎤 Testing different TTS voices: {voices}")
        
        results = {}
        for voice in voices:
            self.logger.info(f"\n--- Testing {voice} voice ---")
            results[voice] = await self.test_audio_generation(lyrics, voice=voice)
        
        # Summary
        passed = sum(results.values())
        total = len(results)
        
        self.logger.info(f"\n📊 Voice Test Results: {passed}/{total} passed")
        for voice, result in results.items():
            status = "✅" if result else "❌"
            self.logger.info(f"   {status} {voice}")
        
        return all(results.values())
    
    async def test_different_beats(self, lyrics: LyricsData) -> bool:
        """Test audio generation with different beat types"""
        beats = ["trap", "boom_bap", "lofi"]
        self.logger.info(f"🥁 Testing different beat types: {beats}")
        
        results = {}
        for beat in beats:
            self.logger.info(f"\n--- Testing {beat} beat ---")
            results[beat] = await self.test_audio_generation(lyrics, beat_type=beat)
        
        # Summary
        passed = sum(results.values())
        total = len(results)
        
        self.logger.info(f"\n📊 Beat Test Results: {passed}/{total} passed")
        for beat, result in results.items():
            status = "✅" if result else "❌"
            self.logger.info(f"   {status} {beat}")
        
        return all(results.values())
    
    def check_api_availability(self) -> bool:
        """Check if required APIs are available"""
        has_openai = self.audio_pipeline.openai_client is not None
        
        self.logger.info(f"🔑 OpenAI TTS API: {'✅ Available' if has_openai else '❌ Missing'}")
        
        if not has_openai:
            self.logger.warning("⚠️  Add OPENAI_API_KEY to your .env file for TTS generation")
            return False
        
        return True
    
    async def run_all_tests(self, lyrics: LyricsData) -> bool:
        """Run comprehensive audio tests"""
        self.logger.info("🚀 Running all audio tests")
        
        # Check API availability
        if not self.check_api_availability():
            self.logger.error("❌ Required APIs not available")
            return False
        
        results = {}
        
        # Test 1: Basic generation
        self.logger.info("\n" + "="*60)
        self.logger.info("TEST 1: Basic Audio Generation")
        self.logger.info("="*60)
        results['basic'] = await self.test_audio_generation(lyrics)
        
        # Test 2: Different voices  
        self.logger.info("\n" + "="*60)
        self.logger.info("TEST 2: Different TTS Voices")
        self.logger.info("="*60)
        results['voices'] = await self.test_different_voices(lyrics)
        
        # Test 3: Different beats
        self.logger.info("\n" + "="*60)
        self.logger.info("TEST 3: Different Beat Types") 
        self.logger.info("="*60)
        results['beats'] = await self.test_different_beats(lyrics)
        
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
    parser = argparse.ArgumentParser(description="Test audio generation from lyrics")
    
    parser.add_argument('--lyrics-file', help='JSON file with generated lyrics')
    parser.add_argument('--voice', choices=['echo', 'alloy', 'nova', 'shimmer'], 
                       default='echo', help='TTS voice to use')
    parser.add_argument('--beat', choices=['trap', 'boom_bap', 'lofi'], 
                       default='trap', help='Beat type')
    parser.add_argument('--test', choices=['single', 'voices', 'beats', 'all'], 
                       default='single', help='Test to run')
    parser.add_argument('--verbose', action='store_true', help='Verbose output')
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging()
    
    tester = AudioTester(verbose=args.verbose)
    
    # Load or create lyrics
    if args.lyrics_file:
        lyrics = tester.load_lyrics_from_file(args.lyrics_file)
        if not lyrics:
            print("❌ Failed to load lyrics file")
            sys.exit(1)
    else:
        print("⚠️  No lyrics file provided, using sample lyrics")
        lyrics = tester.create_sample_lyrics()
    
    try:
        if args.test == 'single':
            success = await tester.test_audio_generation(lyrics, voice=args.voice, beat_type=args.beat)
            
        elif args.test == 'voices':
            success = await tester.test_different_voices(lyrics)
            
        elif args.test == 'beats':
            success = await tester.test_different_beats(lyrics)
            
        elif args.test == 'all':
            success = await tester.run_all_tests(lyrics)
        
        if success:
            print(f"\n🎉 Audio test {'completed successfully' if success else 'failed'}!")
            print("🎵 Check the outputs folder for generated audio files!")
        else:
            print("\n❌ Audio tests failed - check logs above")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n⚠️  Tests interrupted by user")
    except Exception as e:
        print(f"\n❌ Tests failed with error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())