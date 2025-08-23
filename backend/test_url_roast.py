#!/usr/bin/env python3
"""
Test script for Roastify - Test with LinkedIn/Twitter URLs
Usage: python test_url_roast.py --linkedin https://linkedin.com/in/username
       python test_url_roast.py --twitter https://twitter.com/username
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

# Add backend directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

# Import with error handling
try:
    from test_config import TestConfig, SAMPLE_PROFILES, TEST_SCENARIOS, check_api_keys, get_test_mode
    from models import RoastRequest, ProfileData
    from config import setup_logging
    
    # Import components with fallback handling
    try:
        from scraper import ProfileScraper, create_manual_profile
        SCRAPER_AVAILABLE = True
    except ImportError as e:
        print(f"⚠️  Scraper module unavailable: {e}")
        SCRAPER_AVAILABLE = False
        
    try:
        from analyzer import LLMAnalyzer
        ANALYZER_AVAILABLE = True
    except ImportError as e:
        print(f"⚠️  Analyzer module unavailable: {e}")
        ANALYZER_AVAILABLE = False
        
    try:
        from generator import LyricsGenerator
        GENERATOR_AVAILABLE = True
    except ImportError as e:
        print(f"⚠️  Generator module unavailable: {e}")
        GENERATOR_AVAILABLE = False
        
    try:
        from audio import AudioPipeline, create_audio_config
        AUDIO_AVAILABLE = True
    except ImportError as e:
        print(f"⚠️  Audio module unavailable: {e}")
        AUDIO_AVAILABLE = False
        
    try:
        from video import VideoGenerator, VideoConfig
        VIDEO_AVAILABLE = True
    except ImportError as e:
        print(f"⚠️  Video module unavailable: {e}")
        VIDEO_AVAILABLE = False

except ImportError as e:
    print(f"❌ Critical import error: {e}")
    print("\nPlease run the setup script first:")
    print("  ./setup_env.sh")
    print("  conda activate roastify")
    sys.exit(1)


class TestRunner:
    """Main test runner class"""
    
    def __init__(self, verbose: bool = False):
        self.config = TestConfig()
        self.verbose = verbose
        self.run_folder = None
        self.logger = None
        
        # Initialize components (with availability checks)
        self.scraper = ProfileScraper() if SCRAPER_AVAILABLE else None
        self.analyzer = LLMAnalyzer() if ANALYZER_AVAILABLE else None
        self.generator = LyricsGenerator() if GENERATOR_AVAILABLE else None
        self.audio_pipeline = AudioPipeline() if AUDIO_AVAILABLE else None
        self.video_generator = VideoGenerator() if VIDEO_AVAILABLE else None
        
        # Check critical dependencies
        missing_modules = []
        if not SCRAPER_AVAILABLE:
            missing_modules.append("scraper")
        if not ANALYZER_AVAILABLE:
            missing_modules.append("analyzer")
        if not GENERATOR_AVAILABLE:
            missing_modules.append("generator")
            
        if missing_modules:
            print(f"⚠️  Some modules unavailable: {', '.join(missing_modules)}")
            print("The test will use fallback functionality where possible.")
    
    async def run_test(
        self,
        url: Optional[str] = None,
        platform: Optional[str] = None,
        style: str = 'playful',
        beat_type: str = 'trap',
        voice_preference: str = 'echo',
        include_video: bool = True,
        scenario: Optional[str] = None
    ) -> dict:
        """Run a complete test"""
        
        start_time = time.time()
        
        # Setup scenario if provided
        if scenario and scenario in TEST_SCENARIOS:
            scenario_config = TEST_SCENARIOS[scenario]
            style = scenario_config['style']
            beat_type = scenario_config['beat_type']
            voice_preference = scenario_config['voice_preference']
            include_video = scenario_config['include_video']
            print(f"🎭 Using scenario: {scenario} - {scenario_config['description']}")
        
        # Determine platform and name from URL
        if url:
            platform = self.config.get_platform_from_url(url)
            name = self.config.extract_name_from_url(url)
        else:
            # Use sample data
            platform = platform or 'linkedin'
            sample = SAMPLE_PROFILES[platform]
            url = sample['url']
            name = sample['name']
        
        # Create run folder
        self.run_folder = self.config.create_run_folder(platform, name)
        
        # Setup logging
        log_file = self.run_folder / "log.txt"
        self.setup_run_logging(log_file)
        
        self.log(f"🚀 Starting Roastify test run")
        self.log(f"📁 Output folder: {self.run_folder}")
        self.log(f"🔗 URL: {url}")
        self.log(f"🎨 Style: {style}, Beat: {beat_type}, Voice: {voice_preference}")
        self.log(f"🎬 Include video: {include_video}")
        
        # Check API keys
        keys_status = check_api_keys()
        test_mode = get_test_mode()
        self.log(f"🔑 Test mode: {test_mode}")
        
        if self.verbose:
            self.log("API Keys status:")
            for key, status in keys_status.items():
                symbol = "✅" if status['available'] else "❌"
                self.log(f"  {symbol} {key}: {'Available' if status['available'] else 'Missing'}")
        
        results = {
            'start_time': datetime.now().isoformat(),
            'url': url,
            'platform': platform,
            'name': name,
            'style': style,
            'beat_type': beat_type,
            'voice_preference': voice_preference,
            'include_video': include_video,
            'test_mode': test_mode,
            'run_folder': str(self.run_folder),
            'steps': {}
        }
        
        try:
            # Step 1: Scrape/Create Profile
            self.log("📊 Step 1: Getting profile data...")
            step_start = time.time()
            
            pdf_bytes = None
            if url and test_mode in ['full', 'partial']:
                try:
                    profile, pdf_bytes = await self.scraper.scrape_profile(url, as_pdf=True)
                    self.log(f"✅ Profile scraped successfully")
                    if pdf_bytes:
                        self.log(f"✅ PDF generated: {len(pdf_bytes)} bytes")
                    else:
                        self.log(f"⚠️  PDF generation failed, using text-based analysis")
                except Exception as e:
                    self.log(f"⚠️  Scraping failed, using sample data: {e}")
                    profile = self.create_sample_profile(platform, name, url)
                    pdf_bytes = None
            else:
                # Use sample data
                profile = self.create_sample_profile(platform, name, url)
                pdf_bytes = None
            
            # Save profile
            with open(self.run_folder / "profile.json", 'w') as f:
                json.dump(profile.model_dump(), f, indent=2)
            
            # Save PDF if available
            if pdf_bytes:
                with open(self.run_folder / "profile.pdf", 'wb') as f:
                    f.write(pdf_bytes)
                self.log(f"✅ Profile PDF saved")
            
            results['steps']['profile'] = {
                'duration': time.time() - step_start,
                'status': 'completed',
                'name': profile.name
            }
            
            # Step 2: Analyze Profile
            self.log("🧠 Step 2: Analyzing personality...")
            step_start = time.time()
            
            try:
                analysis = await self.analyzer.analyze_profile(profile, pdf_bytes)
                
                # Log which analyzer was used
                if pdf_bytes and self.analyzer.gemini_analyzer:
                    self.log(f"✅ Gemini PDF analysis completed - {len(analysis.roast_angles)} roast angles found")
                else:
                    self.log(f"✅ Text-based analysis completed - {len(analysis.roast_angles)} roast angles found")
                    
            except Exception as e:
                self.log(f"⚠️  AI analysis failed, using fallback: {e}")
                analysis = self.analyzer._create_fallback_analysis(profile)
            
            # Save analysis
            with open(self.run_folder / "analysis.json", 'w') as f:
                json.dump(analysis.model_dump(), f, indent=2)
            
            results['steps']['analysis'] = {
                'duration': time.time() - step_start,
                'status': 'completed',
                'humor_style': analysis.humor_style,
                'roast_angles_count': len(analysis.roast_angles)
            }
            
            # Step 3: Generate Lyrics
            self.log("🎵 Step 3: Writing rap lyrics...")
            step_start = time.time()
            
            try:
                lyrics = await self.generator.generate_lyrics(profile, analysis, style)
                self.log(f"✅ Lyrics generated - Wordplay rating: {lyrics.wordplay_rating:.2f}")
            except Exception as e:
                self.log(f"⚠️  AI lyrics generation failed, using fallback: {e}")
                lyrics = self.generator._create_fallback_lyrics(profile, analysis, style)
            
            # Save lyrics
            with open(self.run_folder / "lyrics.txt", 'w') as f:
                f.write(f"ROAST TRACK FOR: {profile.name}\n")
                f.write(f"Style: {style} | Beat: {beat_type} | BPM: {lyrics.bpm}\n")
                f.write("=" * 50 + "\n\n")
                f.write(lyrics.full_lyrics)
            
            results['steps']['lyrics'] = {
                'duration': time.time() - step_start,
                'status': 'completed',
                'wordplay_rating': lyrics.wordplay_rating,
                'verses_count': len(lyrics.verses)
            }
            
            # Step 4: Generate Audio
            self.log("🔊 Step 4: Creating audio track...")
            step_start = time.time()
            
            audio_config = await create_audio_config(voice_preference, beat_type, style)
            
            try:
                if test_mode == 'full':
                    audio_bytes = await self.audio_pipeline.generate_audio(lyrics, audio_config)
                    self.log(f"✅ Audio generated with OpenAI TTS")
                else:
                    # Create fallback audio (silence for now)
                    audio_bytes = await self.audio_pipeline._generate_fallback_audio(lyrics, audio_config)
                    self.log(f"⚠️  Using fallback audio (no TTS available)")
                
                # Save audio
                audio_path = self.run_folder / "audio.mp3"
                with open(audio_path, 'wb') as f:
                    f.write(audio_bytes)
                
                results['steps']['audio'] = {
                    'duration': time.time() - step_start,
                    'status': 'completed',
                    'file_size': len(audio_bytes),
                    'output_path': str(audio_path)
                }
                
            except Exception as e:
                self.log(f"❌ Audio generation failed: {e}")
                results['steps']['audio'] = {
                    'duration': time.time() - step_start,
                    'status': 'failed',
                    'error': str(e)
                }
                audio_bytes = b""
            
            # Step 5: Generate Video (if requested)
            video_path = None
            if include_video:
                self.log("🎬 Step 5: Creating music video...")
                step_start = time.time()
                
                try:
                    video_config = VideoConfig()
                    video_bytes = await self.video_generator.generate_video(
                        audio_bytes, lyrics, profile, video_config
                    )
                    
                    if video_bytes:
                        video_path = self.run_folder / "video.mp4"
                        with open(video_path, 'wb') as f:
                            f.write(video_bytes)
                        
                        self.log(f"✅ Video generated successfully")
                        results['steps']['video'] = {
                            'duration': time.time() - step_start,
                            'status': 'completed',
                            'file_size': len(video_bytes),
                            'output_path': str(video_path)
                        }
                    else:
                        self.log(f"⚠️  Video generation returned empty result")
                        results['steps']['video'] = {
                            'duration': time.time() - step_start,
                            'status': 'empty'
                        }
                        
                except Exception as e:
                    self.log(f"❌ Video generation failed: {e}")
                    results['steps']['video'] = {
                        'duration': time.time() - step_start,
                        'status': 'failed',
                        'error': str(e)
                    }
            else:
                self.log("⏭️  Skipping video generation (audio-only mode)")
                results['steps']['video'] = {'status': 'skipped'}
            
            # Calculate total time
            total_time = time.time() - start_time
            results['total_duration'] = total_time
            results['end_time'] = datetime.now().isoformat()
            results['status'] = 'completed'
            
            # Save results summary
            with open(self.run_folder / "results.json", 'w') as f:
                json.dump(results, f, indent=2)
            
            # Final summary
            self.log("=" * 50)
            self.log("🎉 TEST COMPLETED SUCCESSFULLY!")
            self.log(f"⏱️  Total time: {total_time:.2f} seconds")
            self.log(f"📁 Output folder: {self.run_folder}")
            self.log("Files created:")
            
            for file_path in self.run_folder.iterdir():
                if file_path.is_file():
                    size = file_path.stat().st_size
                    self.log(f"  📄 {file_path.name} ({self.format_file_size(size)})")
            
            print(f"\n🎯 TEST COMPLETE! Check your results in:")
            print(f"📁 {self.run_folder}")
            
            return results
            
        except Exception as e:
            self.log(f"💥 Test failed with error: {e}")
            results['status'] = 'failed'
            results['error'] = str(e)
            results['total_duration'] = time.time() - start_time
            results['end_time'] = datetime.now().isoformat()
            
            with open(self.run_folder / "results.json", 'w') as f:
                json.dump(results, f, indent=2)
            
            raise
    
    def create_sample_profile(self, platform: str, name: str, url: str) -> ProfileData:
        """Create profile from sample data"""
        if platform in SAMPLE_PROFILES:
            sample = SAMPLE_PROFILES[platform]
            return create_manual_profile(sample['text'], sample['name'])
        else:
            return create_manual_profile(f"Sample user profile for {name}", name)
    
    def setup_run_logging(self, log_file: Path):
        """Setup logging for this run"""
        self.logger = logging.getLogger(f"test_run_{datetime.now().strftime('%H%M%S')}")
        self.logger.setLevel(logging.INFO)
        
        # File handler
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.INFO)
        
        # Console handler (only if verbose)
        if self.verbose:
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.INFO)
            self.logger.addHandler(console_handler)
        
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        
        self.logger.addHandler(file_handler)
    
    def log(self, message: str):
        """Log message with timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] {message}"
        
        if self.logger:
            self.logger.info(message)
        
        if self.verbose:
            print(formatted_message)
        else:
            # Just print key messages without timestamp for clean output
            if any(symbol in message for symbol in ["🚀", "✅", "❌", "🎉", "📁"]):
                print(message)
    
    @staticmethod
    def format_file_size(size_bytes: int) -> str:
        """Format file size in human readable format"""
        if size_bytes == 0:
            return "0 B"
        
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        
        return f"{size_bytes:.1f} TB"


def main():
    """Main CLI function"""
    parser = argparse.ArgumentParser(
        description="Test Roastify with LinkedIn/Twitter URLs",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python test_url_roast.py --linkedin https://linkedin.com/in/johnsmith
  python test_url_roast.py --twitter https://twitter.com/techguru
  python test_url_roast.py --sample linkedin --style aggressive
  python test_url_roast.py --sample twitter --scenario quick --verbose
        """
    )
    
    # Input options
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument('--linkedin', help='LinkedIn profile URL')
    input_group.add_argument('--twitter', help='Twitter/X profile URL')
    input_group.add_argument('--sample', choices=['linkedin', 'twitter'], 
                           help='Use sample profile data')
    
    # Generation options
    parser.add_argument('--style', choices=['playful', 'aggressive', 'witty'],
                       default='playful', help='Roast style (default: playful)')
    parser.add_argument('--beat', choices=['trap', 'boom_bap', 'lofi'],
                       default='trap', help='Beat type (default: trap)')
    parser.add_argument('--voice', choices=['echo', 'alloy', 'fable', 'onyx', 'nova', 'shimmer'],
                       default='echo', help='Voice preference (default: echo)')
    
    # Test options
    parser.add_argument('--scenario', choices=list(TEST_SCENARIOS.keys()),
                       help='Use predefined test scenario')
    parser.add_argument('--audio-only', action='store_true',
                       help='Skip video generation (audio only)')
    parser.add_argument('--verbose', action='store_true',
                       help='Enable verbose logging')
    
    args = parser.parse_args()
    
    # Setup basic logging
    setup_logging()
    
    print("🔥 Roastify URL Test Script")
    print("=" * 40)
    
    # Determine URL and platform
    url = None
    platform = None
    
    if args.linkedin:
        url = args.linkedin
        platform = 'linkedin'
    elif args.twitter:
        url = args.twitter
        platform = 'twitter'
    elif args.sample:
        platform = args.sample
        # URL will be set from sample data
    
    # Create test runner
    runner = TestRunner(verbose=args.verbose)
    
    # Run the test
    try:
        results = asyncio.run(runner.run_test(
            url=url,
            platform=platform,
            style=args.style,
            beat_type=args.beat,
            voice_preference=args.voice,
            include_video=not args.audio_only,
            scenario=args.scenario
        ))
        
        print(f"\n✨ Success! Total time: {results['total_duration']:.1f}s")
        return 0
        
    except KeyboardInterrupt:
        print("\n⛔ Test interrupted by user")
        return 1
    except Exception as e:
        print(f"\n💥 Test failed: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())