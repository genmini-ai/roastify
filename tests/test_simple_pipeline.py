#!/usr/bin/env python3
"""
Test the simplified Roastify pipeline: Scraper → Generator (no analyzer)

Usage:
    python test_simple_pipeline.py --url https://www.linkedin.com/in/username
    python test_simple_pipeline.py --url https://www.linkedin.com/in/username --style aggressive
"""

import argparse
import asyncio
import json
import logging
import sys
import time
from datetime import datetime
from pathlib import Path

# Add backend to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

# Test imports
from scraper import ProfileScraper
from generator import LyricsGenerator
from config import setup_logging

# Test configuration
TEST_OUTPUTS_DIR = Path(__file__).parent / "outputs"


class SimplePipelineTester:
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.scraper = ProfileScraper()
        self.generator = LyricsGenerator()
        self.test_outputs = TEST_OUTPUTS_DIR
        self.test_outputs.mkdir(exist_ok=True)
        
        # Setup logging
        level = logging.DEBUG if verbose else logging.INFO
        logging.basicConfig(level=level, format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)
    
    async def test_full_pipeline(self, url: str, style: str = "playful") -> bool:
        """Test the complete simplified pipeline"""
        if not url:
            self.logger.error("❌ No LinkedIn URL provided")
            return False
        
        self.logger.info(f"🚀 Testing simplified pipeline for: {url}")
        self.logger.info(f"🎭 Style: {style}")
        
        try:
            total_start = time.time()
            
            # Step 1: Scrape profile
            self.logger.info("📊 Step 1: Scraping profile...")
            scrape_start = time.time()
            
            search_result = await self.scraper.scrape_profile_simple(url)
            scrape_duration = time.time() - scrape_start
            
            if "error" in search_result:
                self.logger.error(f"❌ Scraping failed: {search_result.get('error')}")
                return False
            
            self.logger.info(f"✅ Scraping completed in {scrape_duration:.2f}s")
            self.logger.info(f"📄 Title: {search_result.get('title', 'No title')}")
            self.logger.info(f"📝 Description: {search_result.get('description', 'No description')[:100]}...")
            
            # Step 2: Generate lyrics directly from search result
            self.logger.info("🎤 Step 2: Generating rap lyrics...")
            gen_start = time.time()
            
            lyrics = await self.generator.generate_lyrics_from_search(search_result, style)
            gen_duration = time.time() - gen_start
            
            if not lyrics:
                self.logger.error("❌ Lyrics generation failed")
                return False
            
            self.logger.info(f"✅ Lyrics generation completed in {gen_duration:.2f}s")
            self.logger.info(f"🎵 Generated {len(lyrics.verses)} verse(s)")
            self.logger.info(f"🎯 Style: {lyrics.style}")
            self.logger.info(f"🎵 BPM: {lyrics.bpm}")
            
            # Save results
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            results_file = self.test_outputs / f"simple_pipeline_{timestamp}.json"
            lyrics_file = self.test_outputs / f"rap_lyrics_{timestamp}.txt"
            
            # Save complete results
            with open(results_file, 'w') as f:
                json.dump({
                    'url': url,
                    'style': style,
                    'durations': {
                        'scraping': scrape_duration,
                        'generation': gen_duration,
                        'total': time.time() - total_start
                    },
                    'search_result': search_result,
                    'lyrics': lyrics.model_dump(mode='json'),
                    'timestamp': datetime.now().isoformat()
                }, f, indent=2)
            
            # Save formatted lyrics
            with open(lyrics_file, 'w') as f:
                f.write(f"ROAST RAP FOR: {search_result.get('title', 'Unknown')}\n")
                f.write(f"URL: {url}\n")
                f.write(f"Style: {style}\n")
                f.write(f"Generated: {datetime.now().isoformat()}\n")
                f.write("="*60 + "\n\n")
                f.write(lyrics.full_lyrics)
            
            # Display sample lyrics
            self.logger.info("\n🎤 SAMPLE LYRICS:")
            self.logger.info("=" * 50)
            
            if lyrics.intro:
                self.logger.info(f"[INTRO]\n{lyrics.intro[:200]}..." if len(lyrics.intro) > 200 else f"[INTRO]\n{lyrics.intro}")
            
            if lyrics.verses and lyrics.verses[0]:
                verse_preview = lyrics.verses[0][:200] + "..." if len(lyrics.verses[0]) > 200 else lyrics.verses[0]
                self.logger.info(f"\n[VERSE]\n{verse_preview}")
            
            self.logger.info("=" * 50)
            
            total_duration = time.time() - total_start
            self.logger.info(f"📁 Results saved: {results_file}")
            self.logger.info(f"📄 Lyrics saved: {lyrics_file}")
            self.logger.info(f"⏱️  Total time: {total_duration:.2f}s")
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Pipeline failed: {e}")
            if self.verbose:
                import traceback
                traceback.print_exc()
            return False
    
    async def cleanup(self):
        """Cleanup test resources"""
        pass


async def main():
    """Main test function"""
    parser = argparse.ArgumentParser(description="Test simplified Roastify pipeline (Scraper → Generator)")
    
    parser.add_argument('--url', required=True, help='LinkedIn URL to test with')
    parser.add_argument('--style', choices=['aggressive', 'playful', 'witty'], default='playful', help='Roast style')
    parser.add_argument('--verbose', action='store_true', help='Verbose output')
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging()
    
    tester = SimplePipelineTester(verbose=args.verbose)
    
    try:
        success = await tester.test_full_pipeline(args.url, args.style)
        if success:
            print("\n🎉 Simplified pipeline test completed successfully!")
            print("📄 Check the outputs folder for generated lyrics!")
        else:
            print("\n❌ Pipeline test failed - check logs above")
            sys.exit(1)
    finally:
        await tester.cleanup()


if __name__ == "__main__":
    asyncio.run(main())