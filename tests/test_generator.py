#!/usr/bin/env python3
"""
Test module for simplified lyrics generation (no analyzer needed)

Tests the new generate_lyrics_from_search method that works directly with search results.

Usage:
    python test_generator.py --style playful
    python test_generator.py --style aggressive --verbose
    python test_generator.py --test all
"""

import argparse
import asyncio
import json
import logging
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

# Add backend to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

# Test imports
from generator import LyricsGenerator
from models import LyricsData
from config import setup_logging

# Test configuration
TEST_OUTPUTS_DIR = Path(__file__).parent / "outputs"


# Sample search results for testing (mock data)
SAMPLE_SEARCH_RESULTS = {
    "linkedin_ceo": {
        "url": "https://linkedin.com/in/sample-ceo",
        "platform": "linkedin",
        "title": "John Smith - CEO & Founder at TechCorp | Innovation Leader | Thought Leader",
        "description": "Passionate about disrupting industries through synergistic solutions. Building the future of work with AI-powered platforms. Angel investor, mentor, and keynote speaker spreading thought leadership across the ecosystem."
    },
    "linkedin_consultant": {
        "url": "https://linkedin.com/in/sample-consultant", 
        "platform": "linkedin",
        "title": "Sarah Johnson - Digital Transformation Consultant | Helping Companies Scale",
        "description": "Strategic consultant specializing in digital transformation journeys. Helping Fortune 500 companies optimize workflows and leverage cutting-edge technologies for maximum ROI and operational excellence."
    },
    "linkedin_dev": {
        "url": "https://linkedin.com/in/sample-dev",
        "platform": "linkedin", 
        "title": "Mike Chen - Senior Software Engineer at BigTech | Full Stack Developer",
        "description": "Full-stack engineer building scalable systems. Expert in React, Node.js, Python, and cloud architecture. Passionate about clean code, best practices, and mentoring junior developers."
    }
}


class GeneratorTester:
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.generator = LyricsGenerator()
        self.test_outputs = TEST_OUTPUTS_DIR
        self.test_outputs.mkdir(exist_ok=True)
        
        # Setup logging
        level = logging.DEBUG if verbose else logging.INFO
        logging.basicConfig(level=level, format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)
    
    async def test_generation_with_style(self, profile_type: str, style: str) -> bool:
        """Test lyrics generation with a specific style"""
        if profile_type not in SAMPLE_SEARCH_RESULTS:
            self.logger.error(f"❌ Unknown profile type: {profile_type}")
            return False
            
        search_result = SAMPLE_SEARCH_RESULTS[profile_type]
        self.logger.info(f"🎤 Testing {style} style with {profile_type} profile")
        self.logger.info(f"📄 Title: {search_result['title']}")
        self.logger.info(f"📝 Description: {search_result['description'][:100]}...")
        
        try:
            start_time = time.time()
            
            # Generate lyrics using new simplified method
            lyrics = await self.generator.generate_lyrics_from_search(search_result, style)
            
            duration = time.time() - start_time
            
            if not lyrics:
                self.logger.error("❌ Lyrics generation failed")
                return False
            
            # Save results
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = self.test_outputs / f"lyrics_{profile_type}_{style}_{timestamp}.json"
            lyrics_file = self.test_outputs / f"rap_{profile_type}_{style}_{timestamp}.txt"
            
            # Save JSON data
            with open(output_file, 'w') as f:
                json.dump({
                    'profile_type': profile_type,
                    'style': style,
                    'duration': duration,
                    'search_result': search_result,
                    'lyrics': lyrics.model_dump(mode='json'),
                    'timestamp': datetime.now().isoformat()
                }, f, indent=2)
            
            # Save formatted lyrics
            with open(lyrics_file, 'w') as f:
                f.write(f"RAP ROAST - {style.upper()} STYLE\n")
                f.write(f"Target: {search_result['title']}\n")
                f.write(f"Generated: {datetime.now().isoformat()}\n")
                f.write("="*60 + "\n\n")
                f.write(lyrics.full_lyrics)
            
            # Display results
            self.logger.info(f"✅ {style.title()} lyrics generated in {duration:.2f}s")
            self.logger.info(f"🎵 BPM: {lyrics.bpm}")
            self.logger.info(f"📝 Rhyme scheme: {lyrics.rhyme_scheme}")
            self.logger.info(f"⭐ Wordplay rating: {lyrics.wordplay_rating}")
            
            # Show sample lyrics
            if self.verbose or True:  # Always show a sample
                self.logger.info(f"\n🎤 SAMPLE LYRICS ({style.upper()}):")
                self.logger.info("=" * 50)
                
                if lyrics.intro:
                    self.logger.info(f"[INTRO]\n{lyrics.intro}")
                
                if lyrics.verses and lyrics.verses[0]:
                    verse_lines = lyrics.verses[0].split('\n')[:8]  # First 8 lines
                    self.logger.info(f"\n[VERSE - First 8 lines]\n" + '\n'.join(verse_lines))
                    if len(lyrics.verses[0].split('\n')) > 8:
                        self.logger.info("...")
                
                self.logger.info("=" * 50)
            
            self.logger.info(f"📁 Results saved: {output_file}")
            self.logger.info(f"📄 Lyrics saved: {lyrics_file}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Generation failed: {e}")
            if self.verbose:
                import traceback
                traceback.print_exc()
            return False
    
    async def test_all_styles(self, profile_type: str = "linkedin_ceo") -> Dict[str, bool]:
        """Test all available styles"""
        self.logger.info(f"🎭 Testing all styles with {profile_type} profile")
        
        styles = ["playful", "aggressive", "witty"]
        results = {}
        
        for style in styles:
            self.logger.info(f"\n--- Testing {style} style ---")
            results[style] = await self.test_generation_with_style(profile_type, style)
        
        # Summary
        passed = sum(results.values())
        total = len(results)
        
        self.logger.info(f"\n📊 Style Test Results: {passed}/{total} passed")
        for style, result in results.items():
            status = "✅" if result else "❌"
            self.logger.info(f"   {status} {style}")
        
        return results
    
    async def test_different_profiles(self, style: str = "playful") -> Dict[str, bool]:
        """Test with different profile types"""
        self.logger.info(f"👥 Testing different profile types with {style} style")
        
        results = {}
        
        for profile_type in SAMPLE_SEARCH_RESULTS.keys():
            self.logger.info(f"\n--- Testing {profile_type} profile ---")
            results[profile_type] = await self.test_generation_with_style(profile_type, style)
        
        # Summary
        passed = sum(results.values())
        total = len(results)
        
        self.logger.info(f"\n📊 Profile Test Results: {passed}/{total} passed")
        for profile_type, result in results.items():
            status = "✅" if result else "❌"
            self.logger.info(f"   {status} {profile_type}")
        
        return results
    
    async def test_api_fallbacks(self) -> bool:
        """Test API fallback mechanisms"""
        self.logger.info("🔄 Testing API fallback mechanisms")
        
        search_result = SAMPLE_SEARCH_RESULTS["linkedin_dev"]
        
        # Test with both APIs if available
        has_openai = self.generator.openai_client is not None
        has_anthropic = self.generator.anthropic_client is not None
        
        self.logger.info(f"🔑 OpenAI available: {has_openai}")
        self.logger.info(f"🔑 Anthropic available: {has_anthropic}")
        
        if not has_openai and not has_anthropic:
            self.logger.warning("⚠️  No APIs available - testing fallback lyrics only")
            
            # Test fallback
            fallback_lyrics = self.generator._create_simple_fallback_lyrics(search_result, "playful")
            
            if fallback_lyrics and fallback_lyrics.full_lyrics:
                self.logger.info("✅ Fallback lyrics generation works")
                self.logger.info(f"📄 Sample: {fallback_lyrics.intro[:100]}...")
                return True
            else:
                self.logger.error("❌ Fallback lyrics generation failed")
                return False
        
        # Test actual API generation
        try:
            lyrics = await self.generator.generate_lyrics_from_search(search_result, "playful")
            success = lyrics is not None and lyrics.full_lyrics
            
            if success:
                self.logger.info("✅ API generation successful")
            else:
                self.logger.error("❌ API generation failed")
            
            return success
            
        except Exception as e:
            self.logger.error(f"❌ API test failed: {e}")
            return False
    
    async def run_all_tests(self) -> Dict[str, bool]:
        """Run comprehensive generator tests"""
        self.logger.info("🚀 Running all generator tests")
        
        results = {}
        
        # Test 1: Different styles
        self.logger.info("\n" + "="*60)
        self.logger.info("TEST 1: Different Styles")
        self.logger.info("="*60)
        
        style_results = await self.test_all_styles("linkedin_ceo")
        results['all_styles'] = all(style_results.values())
        
        # Test 2: Different profiles  
        self.logger.info("\n" + "="*60)
        self.logger.info("TEST 2: Different Profile Types")
        self.logger.info("="*60)
        
        profile_results = await self.test_different_profiles("playful")
        results['all_profiles'] = all(profile_results.values())
        
        # Test 3: API fallbacks
        self.logger.info("\n" + "="*60)
        self.logger.info("TEST 3: API Fallbacks")
        self.logger.info("="*60)
        
        results['api_fallbacks'] = await self.test_api_fallbacks()
        
        # Overall summary
        passed = sum(results.values())
        total = len(results)
        
        self.logger.info("\n" + "="*60)
        self.logger.info(f"📊 OVERALL RESULTS: {passed}/{total} test categories passed")
        self.logger.info("="*60)
        
        for test_name, result in results.items():
            status = "✅" if result else "❌"
            self.logger.info(f"   {status} {test_name}")
        
        return results


async def main():
    """Main test function"""
    parser = argparse.ArgumentParser(description="Test simplified lyrics generator")
    
    parser.add_argument('--style', choices=['playful', 'aggressive', 'witty'], default='playful', 
                       help='Style to test')
    parser.add_argument('--profile', choices=list(SAMPLE_SEARCH_RESULTS.keys()), default='linkedin_ceo',
                       help='Profile type to test')
    parser.add_argument('--test', choices=['single', 'styles', 'profiles', 'fallbacks', 'all'], default='single',
                       help='Test to run')
    parser.add_argument('--verbose', action='store_true', help='Verbose output')
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging()
    
    tester = GeneratorTester(verbose=args.verbose)
    
    try:
        if args.test == 'single':
            success = await tester.test_generation_with_style(args.profile, args.style)
            print(f"\n🎉 Test {'completed successfully' if success else 'failed'}!")
            
        elif args.test == 'styles':
            results = await tester.test_all_styles(args.profile)
            success = all(results.values())
            print(f"\n🎉 Style tests {'completed successfully' if success else 'had failures'}!")
            
        elif args.test == 'profiles':
            results = await tester.test_different_profiles(args.style)
            success = all(results.values())
            print(f"\n🎉 Profile tests {'completed successfully' if success else 'had failures'}!")
            
        elif args.test == 'fallbacks':
            success = await tester.test_api_fallbacks()
            print(f"\n🎉 Fallback test {'completed successfully' if success else 'failed'}!")
            
        elif args.test == 'all':
            results = await tester.run_all_tests()
            success = all(results.values())
            print(f"\n🎉 All tests {'completed successfully' if success else 'had failures'}!")
            
        if not success:
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n⚠️  Tests interrupted by user")
    except Exception as e:
        print(f"\n❌ Tests failed with error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())